import pytest
from unittest.mock import Mock, patch
from backups.notifications.prometheus import Prometheus

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