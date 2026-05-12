import pytest
from unittest.mock import Mock, patch
from backups.notifications.prometheus import Prometheus
from backups.notifications.golder import Golder

class TestPrometheus:
    def test_init(self):
        config = {
            'url': 'http://prometheus:9091',
            'credentials': {'username': 'user', 'password': 'pass'}
        }
        prom = Prometheus(config)
        assert prom.url == 'http://prometheus:9091'
        assert prom.username == 'user'
        assert prom.password == 'pass'
        assert prom.notify_on_success == True
        assert prom.notify_on_failure == False

    def test_init_no_credentials(self):
        config = {'url': 'http://prometheus:9091'}
        prom = Prometheus(config)
        assert prom.username is None
        assert prom.password is None

    @patch('backups.notifications.prometheus.push_to_gateway')
    @patch('backups.notifications.prometheus.CollectorRegistry')
    @patch('backups.notifications.prometheus.Gauge')
    @patch('backups.notifications.prometheus.Summary')
    def test_notify_success(self, mock_summary, mock_gauge, mock_registry, mock_push):
        config = {'url': 'http://prometheus:9091'}
        prom = Prometheus(config)

        mock_source = Mock()
        mock_source.id = 'testsource'
        hostname = 'testhost'
        filename = 'test.tar'
        mock_stats = Mock()
        mock_stats.size = 1000
        mock_stats.dumptime = 10.0
        mock_stats.uploadtime = 5.0
        mock_stats.retained_copies = ['file1']

        prom.notify_success(mock_source, hostname, filename, mock_stats)

        mock_push.assert_called_once()
        args, kwargs = mock_push.call_args
        assert 'http://prometheus:9091' in args
        assert kwargs['job'] == 'testsource'

    @patch('backups.notifications.prometheus.push_to_gateway')
    def test_notify_success_failure(self, mock_push):
        config = {'url': 'http://prometheus:9091'}
        prom = Prometheus(config)

        mock_push.side_effect = Exception('Push failed')

        mock_source = Mock()
        mock_source.id = 'testsource'
        hostname = 'testhost'
        filename = 'test.tar'
        mock_stats = Mock()
        mock_stats.size = 1000
        mock_stats.dumptime = 10.0
        mock_stats.uploadtime = 5.0
        mock_stats.retained_copies = ['file1']

        # Should not raise, just log error
        prom.notify_success(mock_source, hostname, filename, mock_stats)


class TestGolder:
    def test_init(self):
        config = {
            'url': 'https://backups.golder.tech/v1/backup-runs',
            'token': 'test_token',
            'metadata': {'env': 'test'}
        }
        golder = Golder(config)
        assert golder.url == 'https://backups.golder.tech/v1/backup-runs'
        assert golder.token == 'test_token'
        assert golder.metadata == {'env': 'test'}
        assert golder.notify_on_success == True
        assert golder.notify_on_failure == False

    def test_init_no_token(self):
        config = {'url': 'https://backups.golder.tech/v1/backup-runs'}
        golder = Golder(config)
        assert golder.token is None
        assert golder.metadata == {}

    @patch('backups.notifications.golder.requests.post')
    def test_notify_success(self, mock_post):
        config = {'url': 'https://backups.golder.tech/v1/backup-runs', 'token': 'test_token'}
        golder = Golder(config)

        mock_source = Mock()
        mock_source.name = 'test_job'
        mock_source.encrypted = True
        hostname = 'testhost'
        filename = 'test.tar'
        mock_stats = Mock()
        mock_stats.start_time = Mock()
        mock_stats.start_time.isoformat.return_value = '2023-01-01T00:00:00'
        mock_stats.end_time = Mock()
        mock_stats.end_time.isoformat.return_value = '2023-01-01T00:10:00'
        mock_stats.size = 1000

        golder.notify_success(mock_source, hostname, filename, mock_stats)

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == 'https://backups.golder.tech/v1/backup-runs'
        payload = kwargs['json']
        assert payload['job_name'] == 'test_job'
        assert payload['agent_id'] == 'testhost'
        assert payload['status'] == 'success'
        assert payload['bytes_backed_up'] == 1000
        assert payload['encrypted'] == True
        assert payload['encryption_status'] == 'encrypted'
        assert 'run_id' in payload
        assert payload['metadata'] == {}

    @patch('backups.notifications.golder.requests.post')
    def test_notify_failure(self, mock_post):
        config = {'url': 'https://backups.golder.tech/v1/backup-runs', 'token': 'test_token'}
        golder = Golder(config)

        mock_source = Mock()
        mock_source.name = 'test_job'
        hostname = 'testhost'
        error = Exception('Backup failed')

        golder.notify_failure(mock_source, hostname, error)

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        payload = kwargs['json']
        assert payload['job_name'] == 'test_job'
        assert payload['agent_id'] == 'testhost'
        assert payload['status'] == 'failure'
        assert 'Backup failed' in payload['error']
        assert 'run_id' in payload
        assert payload['metadata'] == {}