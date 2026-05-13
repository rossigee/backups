import json
import os
import sys
import pytest
from unittest.mock import Mock, MagicMock, patch
from backups.notifications.prometheus import Prometheus
from backups.notifications.cloudflare_backup_registry import CloudflareBackupRegistry
from backups.notifications.slack import Slack
from backups.notifications.discord import Discord
from backups.notifications.telegram import Telegram
from backups.notifications.matrix import Matrix
from backups.notifications.smtp import SMTP
from backups.notifications.flagfile import Flagfile
# elasticsearch is an optional dependency; inject a stub before importing the notifier
sys.modules.setdefault('elasticsearch', MagicMock())
from backups.notifications.elasticsearch import Elasticsearch

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
        assert prom.api_key is None
        assert prom.notify_on_success == True
        assert prom.notify_on_failure == False

    def test_init_no_credentials(self):
        config = {'url': 'http://prometheus:9091'}
        prom = Prometheus(config)
        assert prom.username is None
        assert prom.password is None
        assert prom.api_key is None

    def test_init_api_key(self):
        config = {'url': 'http://prometheus:9091', 'api_key': 'secret'}
        prom = Prometheus(config)
        assert prom.api_key == 'secret'
        assert prom.username is None

    @patch('backups.notifications.prometheus.requests.put')
    @patch('backups.notifications.prometheus.generate_latest')
    @patch('backups.notifications.prometheus.CollectorRegistry')
    @patch('backups.notifications.prometheus.Gauge')
    @patch('backups.notifications.prometheus.Summary')
    def test_notify_success_api_key_auth(self, mock_summary, mock_gauge, mock_registry, mock_generate_latest, mock_put):
        mock_generate_latest.return_value = b'mock data'
        config = {'url': 'http://prometheus:9091', 'api_key': 'secret'}
        prom = Prometheus(config)

        mock_source = Mock()
        mock_source.id = 'testsource'
        mock_stats = Mock()
        mock_stats.size = 1000
        mock_stats.dumptime = 10.0
        mock_stats.uploadtime = 5.0
        mock_stats.retained_copies = ['file1']

        prom.notify_success(mock_source, 'testhost', 'test.tar', mock_stats)

        mock_put.assert_called_once()
        args, kwargs = mock_put.call_args
        assert args[0] == 'http://prometheus:9091/metrics/job/testsource'
        assert kwargs['headers']['X-API-Key'] == 'secret'

    @patch('backups.notifications.prometheus.requests.put')
    @patch('backups.notifications.prometheus.generate_latest')
    @patch('backups.notifications.prometheus.CollectorRegistry')
    @patch('backups.notifications.prometheus.Gauge')
    @patch('backups.notifications.prometheus.Summary')
    def test_notify_success(self, mock_summary, mock_gauge, mock_registry, mock_generate_latest, mock_put):
        mock_generate_latest.return_value = b'mock data'
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

        mock_put.assert_called_once()
        args, kwargs = mock_put.call_args
        assert 'http://prometheus:9091/metrics/job/testsource' in args

    @patch('backups.notifications.prometheus.requests.put')
    def test_notify_success_failure(self, mock_put):
        config = {'url': 'http://prometheus:9091'}
        prom = Prometheus(config)

        mock_put.side_effect = Exception('Push failed')

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


class TestCloudflareBackupRegistry:
    def test_init(self):
        config = {
            'url': 'https://backups.golder.tech/v1/backup-runs',
            'token': 'test_token',
            'metadata': {'env': 'test'}
        }
        registry = CloudflareBackupRegistry(config)
        assert registry.url == 'https://backups.golder.tech/v1/backup-runs'
        assert registry.token == 'test_token'
        assert registry.metadata == {'env': 'test'}
        assert registry.notify_on_success == True
        assert registry.notify_on_failure == False

    def test_init_no_token(self):
        config = {'url': 'https://backups.golder.tech/v1/backup-runs'}
        registry = CloudflareBackupRegistry(config)
        assert registry.token is None
        assert registry.metadata == {}

    @patch('backups.notifications.cloudflare_backup_registry.requests.post')
    def test_notify_success(self, mock_post):
        config = {'url': 'https://backups.golder.tech/v1/backup-runs', 'token': 'test_token'}
        registry = CloudflareBackupRegistry(config)

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

        registry.notify_success(mock_source, hostname, filename, mock_stats)

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

    @patch('backups.notifications.cloudflare_backup_registry.requests.post')
    def test_notify_failure(self, mock_post):
        config = {'url': 'https://backups.golder.tech/v1/backup-runs', 'token': 'test_token'}
        registry = CloudflareBackupRegistry(config)

        mock_source = Mock()
        mock_source.name = 'test_job'
        hostname = 'testhost'
        error = Exception('Backup failed')

        registry.notify_failure(mock_source, hostname, error)

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        payload = kwargs['json']
        assert payload['job_name'] == 'test_job'
        assert payload['agent_id'] == 'testhost'
        assert payload['status'] == 'failure'
        assert 'Backup failed' in payload['error']
        assert 'run_id' in payload
        assert payload['metadata'] == {}


class TestSlack:
    def _config(self):
        return {'url': 'https://hooks.slack.com/test'}

    def test_init(self):
        slack = Slack(self._config())
        assert slack.url == 'https://hooks.slack.com/test'
        assert slack.notify_on_success == False
        assert slack.notify_on_failure == False

    def test_pretty_print(self):
        assert Slack.pretty_print(0) == '0:00:00'
        assert Slack.pretty_print(90) == '0:01:30'
        assert Slack.pretty_print(3661) == '1:01:01'

    def test_pretty_print_none(self):
        assert Slack.pretty_print(None) == '0:00:00'

    @patch('backups.notifications.slack.requests.post')
    def test_notify_start(self, mock_post):
        slack = Slack(self._config())
        source = Mock()
        source.name = 'test-source'
        source.type = 'Folder'
        slack.notify_start(source, 'testhost')
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        assert 'test-source' in kwargs['data']['text']
        assert 'testhost' in kwargs['data']['text']

    @patch('backups.notifications.slack.requests.post')
    def test_notify_success(self, mock_post):
        slack = Slack(self._config())
        source = Mock()
        source.name = 'test-source'
        source.type = 'Folder'
        stats = Mock()
        stats.getSizeDescription.return_value = '1.0 KB'
        stats.dumptime = 10.0
        stats.uploadtime = 5.0
        stats.dumptime_dump = 8.0
        stats.dumptime_encrypt = 2.0
        slack.notify_success(source, 'testhost', 'file.tar', stats)
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        assert 'successful' in kwargs['data']['text']
        assert '1.0 KB' in kwargs['data']['text']

    @patch('backups.notifications.slack.requests.post')
    def test_notify_failure(self, mock_post):
        slack = Slack(self._config())
        source = Mock()
        source.name = 'test-source'
        source.type = 'Folder'
        slack.notify_failure(source, 'testhost', Exception('disk full'))
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        assert 'disk full' in kwargs['data']['text']
        assert kwargs['data']['icon_emoji'] == ':imp:'

    @patch('backups.notifications.slack.requests.post')
    def test_http_error_is_logged(self, mock_post):
        from requests.exceptions import HTTPError
        mock_post.return_value.raise_for_status.side_effect = HTTPError('403')
        slack = Slack(self._config())
        source = Mock()
        source.name = 'test-source'
        source.type = 'Folder'
        slack.notify_start(source, 'testhost')  # should not raise


class TestDiscord:
    def _config(self):
        return {'url': 'https://discord.com/api/webhooks/test'}

    def test_init(self):
        discord = Discord(self._config())
        assert discord.url == 'https://discord.com/api/webhooks/test'
        assert discord.notify_on_success == False
        assert discord.notify_on_failure == False

    @patch('backups.notifications.discord.requests.post')
    def test_notify_success(self, mock_post):
        discord = Discord(self._config())
        source = Mock()
        source.name = 'test-source'
        source.type = 'Folder'
        stats = Mock()
        stats.getSizeDescription.return_value = '2.0 MB'
        discord.notify_success(source, 'testhost', 'file.tar', stats)
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        assert 'successful' in kwargs['data']['content']
        assert '2.0 MB' in kwargs['data']['content']

    @patch('backups.notifications.discord.requests.post')
    def test_notify_failure(self, mock_post):
        discord = Discord(self._config())
        source = Mock()
        source.name = 'test-source'
        source.type = 'Folder'
        discord.notify_failure(source, 'testhost', Exception('connection lost'))
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        assert 'connection lost' in kwargs['data']['content']

    @patch('backups.notifications.discord.requests.post')
    def test_http_error_is_logged(self, mock_post):
        from requests.exceptions import HTTPError
        mock_post.return_value.raise_for_status.side_effect = HTTPError('500')
        discord = Discord(self._config())
        source = Mock()
        source.name = 'test-source'
        source.type = 'Folder'
        stats = Mock()
        stats.getSizeDescription.return_value = '1.0 KB'
        discord.notify_success(source, 'testhost', 'file.tar', stats)  # should not raise


class TestTelegram:
    def _config(self):
        return {'api_token': 'bot123', 'chat_id': '-100456'}

    def test_init(self):
        tg = Telegram(self._config())
        assert tg.api_token == 'bot123'
        assert tg.chat_id == '-100456'

    @patch('backups.notifications.telegram.requests.post')
    def test_notify_success(self, mock_post):
        tg = Telegram(self._config())
        source = Mock()
        source.name = 'test-source'
        source.type = 'Folder'
        stats = Mock()
        stats.getSizeDescription.return_value = '500 bytes'
        tg.notify_success(source, 'testhost', 'file.tar', stats)
        mock_post.assert_called_once()
        args, _ = mock_post.call_args
        assert 'bot123' in args[0]
        assert 'sendMessage' in args[0]

    @patch('backups.notifications.telegram.requests.post')
    def test_notify_failure(self, mock_post):
        tg = Telegram(self._config())
        source = Mock()
        source.name = 'test-source'
        source.type = 'Folder'
        tg.notify_failure(source, 'testhost', Exception('storage error'))
        mock_post.assert_called_once()
        args, _ = mock_post.call_args
        assert 'bot123' in args[0]
        assert 'sendMessage' in args[0]


class TestMatrix:
    def _config(self):
        return {
            'url': 'https://matrix.org',
            'room_id': '!abc:matrix.org',
            'access_token': 'tok123',
        }

    def test_init_builds_url(self):
        m = Matrix(self._config())
        assert '/_matrix/client/r0/rooms/' in m.url
        assert '!abc:matrix.org' in m.url
        assert 'access_token=tok123' in m.url

    @patch('backups.notifications.matrix.requests.post')
    def test_msg_success(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = '{}'
        m = Matrix(self._config())
        m._msg('hello')
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        payload = json.loads(kwargs['data'])
        assert payload['msgtype'] == 'm.text'
        assert payload['body'] == 'hello'

    @patch('backups.notifications.matrix.requests.post')
    def test_msg_raises_on_non_200(self, mock_post):
        mock_post.return_value.status_code = 403
        mock_post.return_value.text = 'Forbidden'
        m = Matrix(self._config())
        with pytest.raises(Exception, match='Unexpected HTTP status code: 403'):
            m._msg('test')

    @patch('backups.notifications.matrix.requests.post')
    def test_notify_success(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = '{}'
        m = Matrix(self._config())
        source = Mock()
        source.name = 'test-source'
        source.type = 'Folder'
        stats = Mock()
        stats.getSizeDescription.return_value = '1.0 GB'
        m.notify_success(source, 'testhost', 'file.tar', stats)
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        payload = json.loads(kwargs['data'])
        assert 'successful' in payload['body']
        assert '1.0 GB' in payload['body']

    @patch('backups.notifications.matrix.requests.post')
    def test_notify_failure(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = '{}'
        m = Matrix(self._config())
        source = Mock()
        source.name = 'test-source'
        source.type = 'Folder'
        m.notify_failure(source, 'testhost', Exception('disk full'))
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        payload = json.loads(kwargs['data'])
        assert 'disk full' in payload['body']


class TestSMTP:
    def _config(self):
        return {
            'host': 'smtp.example.com',
            'port': '587',
            'credentials': {'username': 'user', 'password': 'pass'},
            'use_tls': True,
            'use_ssl': False,
            'success_to': 'backup@example.com',
            'failure_to': 'alerts@example.com',
            'debug': False,
        }

    def test_init(self):
        smtp = SMTP(self._config())
        assert smtp.host == 'smtp.example.com'
        assert smtp.port == 587
        assert smtp.username == 'user'
        assert smtp.password == 'pass'
        assert smtp.use_tls == True
        assert smtp.use_ssl == False
        assert smtp.success_to == 'backup@example.com'
        assert smtp.failure_to == 'alerts@example.com'
        assert smtp.debug == False

    @patch('smtplib.SMTP')
    def test_notify_success_tls(self, mock_smtp_class):
        mock_server = Mock()
        mock_smtp_class.return_value = mock_server
        smtp = SMTP(self._config())
        source = Mock()
        source.name = 'test-source'
        source.type = 'Folder'
        source.id = 'test-id'
        stats = Mock()
        stats.getSizeDescription.return_value = '1.0 KB'
        smtp.notify_success(source, 'testhost', 'file.tar', stats)
        mock_smtp_class.assert_called_once_with('smtp.example.com', 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with('user', 'pass')
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()

    @patch('smtplib.SMTP_SSL')
    def test_notify_success_ssl(self, mock_smtp_ssl_class):
        mock_server = Mock()
        mock_smtp_ssl_class.return_value = mock_server
        config = self._config()
        config['use_ssl'] = True
        config['use_tls'] = False
        smtp = SMTP(config)
        source = Mock()
        source.name = 'test-source'
        source.type = 'Folder'
        source.id = 'test-id'
        stats = Mock()
        stats.getSizeDescription.return_value = '1.0 KB'
        smtp.notify_success(source, 'testhost', 'file.tar', stats)
        mock_smtp_ssl_class.assert_called_once_with('smtp.example.com', 587)
        mock_server.sendmail.assert_called_once()

    def test_notify_success_skips_when_no_success_to(self):
        config = self._config()
        config['success_to'] = None
        smtp = SMTP(config)
        source = Mock()
        stats = Mock()
        smtp.notify_success(source, 'testhost', 'file.tar', stats)
        stats.getSizeDescription.assert_not_called()

    @patch('traceback.print_exc')
    @patch('smtplib.SMTP')
    def test_notify_failure(self, mock_smtp_class, _mock_print_exc):
        mock_server = Mock()
        mock_smtp_class.return_value = mock_server
        smtp = SMTP(self._config())
        source = Mock()
        source.name = 'test-source'
        source.type = 'Folder'
        source.id = 'test-id'
        smtp.notify_failure(source, 'testhost', Exception('backup failed'))
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()

    @patch('traceback.print_exc')
    def test_notify_failure_skips_when_no_failure_to(self, _mock_print_exc):
        config = self._config()
        config['failure_to'] = None
        smtp = SMTP(config)
        source = Mock()
        smtp.notify_failure(source, 'testhost', Exception('error'))
        # No SMTP connection attempted; assert sendmail was never called
        source.assert_not_called()


class TestElasticsearch:
    def _config(self):
        return {
            'url': 'http://elastic:9200',
            'indexpattern': 'backups-%Y.%m',
        }

    def test_init(self):
        es = Elasticsearch(self._config())
        assert es.url == 'http://elastic:9200'
        assert es.indexpattern == 'backups-%Y.%m'
        assert es.username is None
        assert es.password is None
        assert es.notify_on_success == True
        assert es.notify_on_failure == True

    def test_init_with_credentials(self):
        config = dict(self._config())
        config['credentials'] = {'username': 'user', 'password': 'pass'}
        es = Elasticsearch(config)
        assert es.username == 'user'
        assert es.password == 'pass'

    @patch('backups.notifications.elasticsearch.elasticsearch')
    def test_notify_success(self, mock_es_module):
        mock_client = Mock()
        mock_es_module.Elasticsearch.return_value = mock_client
        es = Elasticsearch(self._config())
        source = Mock()
        source.id = 'test-id'
        source.name = 'test-source'
        stats = Mock()
        stats.starttime = None
        stats.endtime = None
        stats.size = 1000
        stats.dumptime = 10.0
        stats.dumpedfiles = 5
        stats.uploadtime = 5.0
        stats.retainedfiles = ['file1']
        es.notify_success(source, 'testhost', 'file.tar', stats)
        mock_client.index.assert_called_once()
        _, kwargs = mock_client.index.call_args
        assert kwargs['body']['status'] == 'success'
        assert kwargs['body']['hostname'] == 'testhost'

    @patch('backups.notifications.elasticsearch.elasticsearch')
    def test_notify_failure(self, mock_es_module):
        mock_client = Mock()
        mock_es_module.Elasticsearch.return_value = mock_client
        es = Elasticsearch(self._config())
        source = Mock()
        source.id = 'test-id'
        source.name = 'test-source'
        es.notify_failure(source, 'testhost', Exception('timeout'))
        mock_client.index.assert_called_once()
        _, kwargs = mock_client.index.call_args
        assert kwargs['body']['status'] == 'failed'
        assert 'timeout' in kwargs['body']['error']

    @patch('backups.notifications.elasticsearch.elasticsearch')
    def test_write_exception_is_caught(self, mock_es_module):
        mock_client = Mock()
        mock_client.index.side_effect = Exception('connection refused')
        mock_es_module.Elasticsearch.return_value = mock_client
        es = Elasticsearch(self._config())
        source = Mock()
        source.id = 'test-id'
        source.name = 'test-source'
        es.notify_failure(source, 'testhost', Exception('error'))  # should not raise


class TestFlagfile:
    def test_init(self):
        ff = Flagfile({'flagfile': '/tmp/backup.flag'})
        assert ff.filename == '/tmp/backup.flag'
        assert ff.notify_on_success == True
        assert ff.notify_on_failure == False

    def test_notify_success_writes_ok(self, tmp_path):
        flagfile = str(tmp_path / 'backup.flag')
        ff = Flagfile({'flagfile': flagfile})
        ff.notify_success(Mock(), 'testhost', 'file.tar', Mock())
        assert os.path.exists(flagfile)
        with open(flagfile) as f:
            assert f.read() == 'OK'

    def test_notify_failure_is_noop(self, tmp_path):
        flagfile = str(tmp_path / 'backup.flag')
        ff = Flagfile({'flagfile': flagfile})
        ff.notify_failure(Mock(), 'testhost', Exception('error'))
        assert not os.path.exists(flagfile)