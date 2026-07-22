"""
Unit Tests for Analytics Service Layer.
Verifies fetching live stats and executing read_sql using mocked engines.
"""

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from src.services.analytics import AnalyticsService

@pytest.fixture
def mock_engine():
    """Provides a mocked SQLAlchemy engine for testing."""
    with patch("src.services.analytics.get_engine") as mock_get:
        engine = MagicMock()
        mock_get.return_value = engine
        yield engine

def test_get_total_users(mock_engine):
    """Verifies retrieval of total registered users."""
    mock_df = pd.DataFrame({"count": [12500]})
    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        service = AnalyticsService()
        result = service.get_total_users()
        assert result == 12500
        mock_read.assert_called_once()

def test_get_total_marketing_events(mock_engine):
    """Verifies retrieval of total marketing events."""
    mock_df = pd.DataFrame({"count": [45000]})
    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        service = AnalyticsService()
        result = service.get_total_marketing_events()
        assert result == 45000
        mock_read.assert_called_once()

def test_get_total_applications(mock_engine):
    """Verifies retrieval of total applications."""
    mock_df = pd.DataFrame({"count": [8200]})
    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        service = AnalyticsService()
        result = service.get_total_applications()
        assert result == 8200
        mock_read.assert_called_once()

def test_get_total_disbursed(mock_engine):
    """Verifies retrieval of total disbursed loans."""
    mock_df = pd.DataFrame({"count": [3100]})
    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        service = AnalyticsService()
        result = service.get_total_disbursed()
        assert result == 3100
        mock_read.assert_called_once()

def test_get_approval_rate(mock_engine):
    """Verifies calculation of loan approval rate."""
    mock_df = pd.DataFrame({"rate": [72.5]})
    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        service = AnalyticsService()
        result = service.get_approval_rate()
        assert result == 72.5
        mock_read.assert_called_once()

def test_get_average_loan_amount(mock_engine):
    """Verifies calculation of average loan amount."""
    mock_df = pd.DataFrame({"avg_amt": [65000.0]})
    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        service = AnalyticsService()
        result = service.get_average_loan_amount()
        assert result == 65000.0
        mock_read.assert_called_once()

def test_get_funnel_data(mock_engine):
    """Verifies retrieval of funnel stage volumes."""
    mock_df = pd.DataFrame({
        "stage_num": [1, 2],
        "stage_name": ["Impression", "Click"],
        "unique_users": [10000, 5000],
        "pct_of_tof": [100.0, 50.0],
        "pct_of_previous": [100.0, 50.0]
    })
    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        service = AnalyticsService()
        result = service.get_funnel_data()
        assert len(result) == 2
        assert list(result["stage_name"]) == ["Impression", "Click"]
        mock_read.assert_called_once()

def test_get_stage_conversion(mock_engine):
    """Verifies retrieval of stage-to-stage conversion rates."""
    mock_df = pd.DataFrame({
        "transition": ["App Open -> Signup"],
        "conversion_rate": [80.0]
    })
    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        service = AnalyticsService()
        result = service.get_stage_conversion()
        assert len(result) == 1
        assert result["conversion_rate"].iloc[0] == 80.0
        mock_read.assert_called_once()

def test_get_overall_conversion(mock_engine):
    """Verifies retrieval of overall funnel conversion rate."""
    mock_df = pd.DataFrame({
        "app_open": [1000],
        "disbursed": [20],
        "conversion_rate": [2.00]
    })
    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        service = AnalyticsService()
        result = service.get_overall_conversion()
        assert len(result) == 1
        assert result["conversion_rate"].iloc[0] == 2.00
        mock_read.assert_called_once()

def test_get_marketing_kpis(mock_engine):
    """Verifies retrieval of high-level marketing KPI metrics."""
    mock_df = pd.DataFrame({
        "total_campaigns": [5],
        "total_spend": [150000.0],
        "total_revenue": [300000.0],
        "overall_roi_pct": [100.0],
        "average_cac": [250.0]
    })
    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        service = AnalyticsService()
        result = service.get_marketing_kpis()
        assert len(result) == 1
        assert result["total_campaigns"].iloc[0] == 5
        assert result["overall_roi_pct"].iloc[0] == 100.0
        mock_read.assert_called_once()

def test_get_roi_by_channel(mock_engine):
    """Verifies retrieval of channel-level ROI."""
    mock_df = pd.DataFrame({
        "acquisition_channel": ["Google Ads"],
        "roi_pct": [120.0]
    })
    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        service = AnalyticsService()
        result = service.get_roi_by_channel()
        assert len(result) == 1
        assert result["roi_pct"].iloc[0] == 120.0
        mock_read.assert_called_once()

def test_get_spend_vs_revenue(mock_engine):
    """Verifies retrieval of channel-level spend and revenue."""
    mock_df = pd.DataFrame({
        "acquisition_channel": ["Google Ads"],
        "marketing_spend": [50000.0],
        "estimated_revenue": [110000.0]
    })
    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        service = AnalyticsService()
        result = service.get_spend_vs_revenue()
        assert len(result) == 1
        assert result["marketing_spend"].iloc[0] == 50000.0
        mock_read.assert_called_once()

def test_get_cac_by_channel(mock_engine):
    """Verifies retrieval of channel-level CAC."""
    mock_df = pd.DataFrame({
        "acquisition_channel": ["Google Ads"],
        "marketing_spend": [50000.0],
        "acquired_customers": [200],
        "customer_acquisition_cost": [250.0]
    })
    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        service = AnalyticsService()
        result = service.get_cac_by_channel()
        assert len(result) == 1
        assert result["customer_acquisition_cost"].iloc[0] == 250.0
        mock_read.assert_called_once()

def test_get_campaign_performance(mock_engine):
    """Verifies retrieval of campaign-level metrics."""
    mock_df = pd.DataFrame({
        "campaign": ["Campaign A"],
        "channel": ["Google Ads"],
        "campaign_spend": [10000.0],
        "total_installs": [1000],
        "signups": [500],
        "disbursements": [50],
        "cac": [200.0],
        "install_to_signup_rate_pct": [50.0],
        "signup_to_disbursed_rate_pct": [10.0]
    })
    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        service = AnalyticsService()
        result = service.get_campaign_performance()
        assert len(result) == 1
        assert result["campaign"].iloc[0] == "Campaign A"
        assert result["cac"].iloc[0] == 200.0
        mock_read.assert_called_once()

def test_get_customer_kpis(mock_engine):
    """Verifies retrieval of customer summary KPIs."""
    mock_df = pd.DataFrame({
        "total_customers": [10000],
        "avg_income": [55000.0],
        "avg_cibil": [720.0],
        "active_states": [15]
    })
    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        service = AnalyticsService()
        result = service.get_customer_kpis()
        assert len(result) == 1
        assert result["total_customers"].iloc[0] == 10000
        assert result["avg_cibil"].iloc[0] == 720.0
        mock_read.assert_called_once()

def test_get_cibil_distribution(mock_engine):
    """Verifies retrieval of CIBIL score distribution."""
    mock_df = pd.DataFrame({"cibil_score": [700, 750, 800]})
    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        service = AnalyticsService()
        result = service.get_cibil_distribution()
        assert len(result) == 3
        mock_read.assert_called_once()

def test_get_income_distribution(mock_engine):
    """Verifies retrieval of monthly income distribution."""
    mock_df = pd.DataFrame({"monthly_income": [35000.0, 45000.0]})
    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        service = AnalyticsService()
        result = service.get_income_distribution()
        assert len(result) == 2
        mock_read.assert_called_once()

def test_get_state_distribution(mock_engine):
    """Verifies retrieval of user count by state."""
    mock_df = pd.DataFrame({
        "state": ["Maharashtra", "Karnataka"],
        "user_count": [1200, 800]
    })
    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        service = AnalyticsService()
        result = service.get_state_distribution()
        assert len(result) == 2
        assert result["state"].iloc[0] == "Maharashtra"
        mock_read.assert_called_once()

def test_get_occupation_distribution(mock_engine):
    """Verifies retrieval of user count by occupation."""
    mock_df = pd.DataFrame({
        "occupation": ["Salaried", "Self-Employed"],
        "user_count": [2500, 1500]
    })
    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        service = AnalyticsService()
        result = service.get_occupation_distribution()
        assert len(result) == 2
        assert result["occupation"].iloc[0] == "Salaried"
        mock_read.assert_called_once()

def test_get_device_distribution(mock_engine):
    """Verifies retrieval of user count by device platform."""
    mock_df = pd.DataFrame({
        "device_platform": ["Android", "iOS"],
        "user_count": [3000, 1000]
    })
    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        service = AnalyticsService()
        result = service.get_device_distribution()
        assert len(result) == 2
        assert result["device_platform"].iloc[0] == "Android"
        mock_read.assert_called_once()

def test_get_age_distribution(mock_engine):
    """Verifies retrieval of age distribution."""
    mock_df = pd.DataFrame({"age": [25, 30, 35]})
    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        service = AnalyticsService()
        result = service.get_age_distribution()
        assert len(result) == 3
        mock_read.assert_called_once()

def test_get_experiment_kpis(mock_engine):
    """Verifies retrieval of experiment KPIs."""
    mock_df = pd.DataFrame({
        "total_experiments": [3],
        "winning_variants": [1],
        "avg_lift_pct": [2.5],
        "total_revenue_lift": [15000.0]
    })
    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        service = AnalyticsService()
        result = service.get_experiment_kpis()
        assert len(result) == 1
        assert result["total_experiments"].iloc[0] == 3
        assert result["winning_variants"].iloc[0] == 1
        mock_read.assert_called_once()

def test_get_experiment_results(mock_engine):
    """Verifies retrieval of Control vs Treatment results."""
    mock_df = pd.DataFrame({
        "experiment_name": ["KYC Flow", "KYC Flow"],
        "variant": ["Control", "Treatment"],
        "sample_size": [5000, 5000],
        "conversions": [350, 400],
        "conversion_rate": [7.0, 8.0]
    })
    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        service = AnalyticsService()
        result = service.get_experiment_results()
        assert len(result) == 2
        assert result["variant"].iloc[0] == "Control"
        mock_read.assert_called_once()

def test_get_conversion_lift(mock_engine):
    """Verifies retrieval of conversion lifts."""
    mock_df = pd.DataFrame({
        "experiment_name": ["KYC Flow"],
        "lift_pct": [14.28]
    })
    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        service = AnalyticsService()
        result = service.get_conversion_lift()
        assert len(result) == 1
        assert result["lift_pct"].iloc[0] == 14.28
        mock_read.assert_called_once()

def test_get_revenue_lift(mock_engine):
    """Verifies retrieval of incremental revenue lifts."""
    mock_df = pd.DataFrame({
        "experiment_name": ["KYC Flow"],
        "incremental_revenue": [15000.0]
    })
    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        service = AnalyticsService()
        result = service.get_revenue_lift()
        assert len(result) == 1
        assert result["incremental_revenue"].iloc[0] == 15000.0
        mock_read.assert_called_once()

def test_get_confidence_scores(mock_engine):
    """Verifies retrieval of statistical confidence scores."""
    mock_df = pd.DataFrame({
        "experiment_name": ["KYC Flow"],
        "z_score": [2.10],
        "abs_z_score": [2.10],
        "significance_status": ["Significant"],
        "recommendation": ["Ship"]
    })
    with patch("pandas.read_sql", return_value=mock_df) as mock_read:
        service = AnalyticsService()
        result = service.get_confidence_scores()
        assert len(result) == 1
        assert result["recommendation"].iloc[0] == "Ship"
        mock_read.assert_called_once()




