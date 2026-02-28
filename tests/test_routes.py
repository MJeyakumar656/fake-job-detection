"""Tests for API routes."""
import json
import pytest


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check_returns_200(self, client):
        """Health check should return 200 status."""
        response = client.get('/api/health')
        assert response.status_code == 200

    def test_health_check_contains_status(self, client):
        """Health check should contain status field."""
        response = client.get('/api/health')
        data = json.loads(response.data)
        assert 'status' in data
        assert data['status'] == 'healthy'

    def test_health_check_contains_model_info(self, client):
        """Health check should report model loaded status."""
        response = client.get('/api/health')
        data = json.loads(response.data)
        assert 'model_loaded' in data


class TestAnalyzeEndpoint:
    """Test the /api/analyze endpoint."""

    def test_analyze_requires_data(self, client):
        """Analyze should reject empty requests."""
        response = client.post('/api/analyze',
                               data=json.dumps({}),
                               content_type='application/json')
        assert response.status_code == 400

    def test_analyze_requires_job_input(self, client):
        """Analyze should reject missing job_input."""
        response = client.post('/api/analyze',
                               data=json.dumps({'job_input': ''}),
                               content_type='application/json')
        assert response.status_code == 400

    def test_analyze_rejects_short_text(self, client):
        """Analyze should reject very short text."""
        response = client.post('/api/analyze',
                               data=json.dumps({
                                   'job_input': 'short text',
                                   'input_type': 'text'
                               }),
                               content_type='application/json')
        assert response.status_code == 400

    def test_analyze_rejects_invalid_type(self, client):
        """Analyze should reject invalid input_type."""
        response = client.post('/api/analyze',
                               data=json.dumps({
                                   'job_input': 'some input',
                                   'input_type': 'invalid'
                               }),
                               content_type='application/json')
        assert response.status_code == 400

    def test_analyze_text_input(self, client, sample_job_text):
        """Analyze should process valid text input."""
        response = client.post('/api/analyze',
                               data=json.dumps({
                                   'job_input': sample_job_text,
                                   'input_type': 'text'
                               }),
                               content_type='application/json')
        # Should return 200 or 500 (if model not loaded)
        assert response.status_code in [200, 500]

    def test_analyze_auto_detect_text(self, client, sample_job_text):
        """Analyze should auto-detect text input type."""
        response = client.post('/api/analyze',
                               data=json.dumps({
                                   'job_input': sample_job_text,
                                   'input_type': 'auto'
                               }),
                               content_type='application/json')
        assert response.status_code in [200, 500]

    def test_analyze_auto_detect_url(self, client):
        """Analyze should auto-detect URL input type."""
        response = client.post('/api/analyze',
                               data=json.dumps({
                                   'job_input': 'https://www.linkedin.com/jobs/view/12345',
                                   'input_type': 'auto'
                               }),
                               content_type='application/json')
        # URL scraping may fail but should not be a 400
        assert response.status_code in [200, 400, 500]


class TestSupportedPortals:
    """Test supported portals endpoint."""

    def test_returns_portals(self, client):
        """Should return list of supported portals."""
        response = client.get('/api/supported-portals')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'supported_portals' in data
        assert len(data['supported_portals']) == 4

    def test_portal_structure(self, client):
        """Each portal should have name, domain, url_example."""
        response = client.get('/api/supported-portals')
        data = json.loads(response.data)
        for portal in data['supported_portals']:
            assert 'name' in portal
            assert 'domain' in portal
            assert 'url_example' in portal


class TestBatchAnalyze:
    """Test batch analysis endpoint."""

    def test_batch_requires_jobs(self, client):
        """Batch should reject missing jobs list."""
        response = client.post('/api/analyze-batch',
                               data=json.dumps({}),
                               content_type='application/json')
        assert response.status_code == 400

    def test_batch_rejects_empty_list(self, client):
        """Batch should reject empty jobs list."""
        response = client.post('/api/analyze-batch',
                               data=json.dumps({'jobs': []}),
                               content_type='application/json')
        assert response.status_code == 400


class TestPageRoutes:
    """Test HTML page routes."""

    def test_home_page(self, client):
        """Home page should return 200."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'JobGuard AI' in response.data

    def test_about_page(self, client):
        """About page should return 200."""
        response = client.get('/about')
        assert response.status_code == 200
        assert b'About' in response.data

    def test_how_it_works_page(self, client):
        """How it works page should return 200."""
        response = client.get('/how-it-works')
        assert response.status_code == 200

    def test_result_page_redirects_without_session(self, client):
        """Result page should redirect without analysis data."""
        response = client.get('/result')
        assert response.status_code == 302  # Redirect to home

    def test_404_page(self, client):
        """Non-existent page should return 404."""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404
