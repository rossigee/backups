import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from backups.compress import compress
from backups.encrypt import encrypt
from backups.stats import BackupRunStatistics
from backups.exceptions import BackupException
import backups.main

class TestCompress:
    @patch('subprocess.Popen')
    def test_compress_success(self, mock_popen):
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, 'test.tar')
            with open(filename, 'w') as f:
                f.write('test')

            result = compress(filename)
            expected = filename + '.gz'
            assert result == expected

    @patch('subprocess.Popen')
    def test_compress_failure(self, mock_popen):
        mock_proc = Mock()
        mock_proc.returncode = 1
        mock_popen.return_value = mock_proc

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, 'test.tar')
            with open(filename, 'w') as f:
                f.write('test')

            with pytest.raises(BackupException, match="Error while compressing"):
                compress(filename)

class TestEncrypt:
    @patch('subprocess.Popen')
    def test_encrypt_passphrase(self, mock_popen):
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, 'test.tar')
            with open(filename, 'w') as f:
                f.write('test')

            result = encrypt(filename, passphrase='testpass')
            expected = filename + '.gpg'
            assert result == expected

    @patch('subprocess.Popen')
    def test_encrypt_recipients(self, mock_popen):
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, 'test.tar')
            with open(filename, 'w') as f:
                f.write('test')

            result = encrypt(filename, recipients=['user@example.com'])
            expected = filename + '.gpg'
            assert result == expected

    def test_encrypt_no_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, 'test.tar')
            with open(filename, 'w') as f:
                f.write('test')

            with pytest.raises(BackupException, match="Misconfigured encryption"):
                encrypt(filename)

class TestBackupRunStatistics:
    def test_init(self):
        stats = BackupRunStatistics()
        assert stats.starttime is None
        assert stats.endtime is None
        assert stats.size is None
        assert stats.dumpedfiles == []
        assert stats.dumptime is None
        assert stats.uploadtime is None
        assert stats.retained_copies == []

    @pytest.mark.parametrize("size,expected", [
        (100, "100.0 bytes"),
        (1024, "1.0 KB"),
        (1024*1024, "1.0 MB"),
        (1024*1024*1024, "1.0 GB"),
        (1024*1024*1024*1024, "1.0 TB"),
    ])
    def test_getSizeDescription(self, size, expected):
        stats = BackupRunStatistics()
        stats.size = size
        assert stats.getSizeDescription() == expected

otel = pytest.importorskip("opentelemetry", reason="opentelemetry-sdk not installed")

from opentelemetry.sdk.trace import TracerProvider as _TracerProvider
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from backups.main import BackupRunInstance


def _make_test_tracer():
    exporter = InMemorySpanExporter()
    provider = _TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return provider.get_tracer("test"), exporter


class TestTracing:
    def _make_instance(self, tracer):
        instance = BackupRunInstance()
        instance.tracer = tracer
        instance.sources = []
        instance.destinations = []
        instance.notifications = []
        return instance

    def test_backup_run_span_created(self):
        tracer, exporter = _make_test_tracer()
        instance = self._make_instance(tracer)
        instance.run()
        names = [s.name for s in exporter.get_finished_spans()]
        assert "backup_run" in names

    def test_source_spans_created(self):
        tracer, exporter = _make_test_tracer()
        instance = self._make_instance(tracer)

        mock_source = Mock()
        mock_source.id = "src-1"
        mock_source.name = "Test Source"
        mock_source.dump_and_compress.return_value = []
        instance.sources = [mock_source]

        instance.run()
        names = [s.name for s in exporter.get_finished_spans()]
        assert "process_source" in names
        assert "dump_and_compress" in names
        assert "upload_files" in names

    def test_span_attributes_set_inside_span(self):
        tracer, exporter = _make_test_tracer()
        instance = self._make_instance(tracer)

        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"data")
            tmpfile = f.name

        try:
            mock_source = Mock()
            mock_source.id = "src-1"
            mock_source.name = "Test Source"
            mock_source.dump_and_compress.return_value = [tmpfile]

            mock_dest = Mock()
            mock_dest.send.return_value = tmpfile
            mock_dest.cleanup.return_value = []
            instance.sources = [mock_source]
            instance.destinations = [mock_dest]

            instance.run()

            spans = {s.name: s for s in exporter.get_finished_spans()}
            dump_span = spans["dump_and_compress"]
            assert dump_span.attributes["file.count"] == 1
            assert dump_span.attributes["total.size"] == 4
            assert "dumptime" in dump_span.attributes

            upload_span = spans["upload_files"]
            assert upload_span.attributes["dumped.count"] == 1
            assert "uploadtime" in upload_span.attributes
        finally:
            if os.path.exists(tmpfile):
                os.unlink(tmpfile)

    def test_failure_notification_on_source_error(self):
        tracer, exporter = _make_test_tracer()
        instance = self._make_instance(tracer)

        mock_source = Mock()
        mock_source.id = "src-1"
        mock_source.name = "Test Source"
        mock_source.dump_and_compress.side_effect = RuntimeError("disk full")
        instance.sources = [mock_source]

        mock_notification = Mock()
        instance.notifications = [mock_notification]

        instance.run()

        mock_notification._notify_failure.assert_called_once()
        names = [s.name for s in exporter.get_finished_spans()]
        assert "notify_failure" in names

    def test_notification_error_does_not_crash_run(self):
        tracer, exporter = _make_test_tracer()
        instance = self._make_instance(tracer)

        mock_source = Mock()
        mock_source.id = "src-1"
        mock_source.name = "Test Source"
        mock_source.dump_and_compress.return_value = []
        instance.sources = [mock_source]

        mock_notification = Mock()
        mock_notification._notify_success.side_effect = RuntimeError("notify down")
        instance.notifications = [mock_notification]

        instance.run()

    def test_noop_tracer_when_otel_disabled(self):
        instance = BackupRunInstance()
        assert isinstance(instance.tracer, backups.main._NoOpTracer)
        mock_source = Mock()
        mock_source.id = "src-1"
        mock_source.name = "Test"
        mock_source.dump_and_compress.return_value = []
        instance.sources = [mock_source]
        instance.destinations = []
        instance.notifications = []
        instance.run()


class TestApplyDefaultEncryption:
    def test_global_passphrase_applied_to_source(self):
        src = {'type': 'mysql', 'name': 'db'}
        result = backups.main._apply_default_encryption(src, {'passphrase': 'secret'})
        assert result['passphrase'] == 'secret'

    def test_global_recipients_applied_to_source(self):
        src = {'type': 'mysql', 'name': 'db'}
        result = backups.main._apply_default_encryption(src, {'recipients': ['ops@example.com']})
        assert result['recipients'] == ['ops@example.com']

    def test_per_source_passphrase_overrides_global(self):
        src = {'type': 'mysql', 'name': 'db', 'passphrase': 'mine'}
        result = backups.main._apply_default_encryption(src, {'passphrase': 'global'})
        assert result['passphrase'] == 'mine'

    def test_per_source_recipients_overrides_global(self):
        src = {'type': 'mysql', 'name': 'db', 'recipients': ['local@example.com']}
        result = backups.main._apply_default_encryption(src, {'recipients': ['global@example.com']})
        assert result['recipients'] == ['local@example.com']

    def test_per_source_passphrase_blocks_global_recipients(self):
        src = {'type': 'mysql', 'name': 'db', 'passphrase': 'mine'}
        result = backups.main._apply_default_encryption(src, {'recipients': ['global@example.com']})
        assert 'recipients' not in result

    def test_no_global_encryption(self):
        src = {'type': 'mysql', 'name': 'db'}
        result = backups.main._apply_default_encryption(src, {})
        assert 'passphrase' not in result
        assert 'recipients' not in result

    def test_original_config_not_mutated(self):
        src = {'type': 'mysql', 'name': 'db'}
        backups.main._apply_default_encryption(src, {'passphrase': 'secret'})
        assert 'passphrase' not in src