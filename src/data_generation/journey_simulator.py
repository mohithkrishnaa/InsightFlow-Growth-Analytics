# Journey Simulation Engine Module for the InsightFlow Data Generation Pipeline
"""
This module contains the Journey Simulation Engine responsible for simulating the complete
customer lifecycle journey (Marketing, Application, and Loan stages) for synthetic users.
It produces three event datasets: marketing events, app events, and loan events.
"""

import os
import logging
import argparse
import sys
import pandas as pd
import numpy as np
from abc import ABC
from typing import Dict, Any, Tuple, List

from src.data_generation.config import AppConfig, load_config
from src.data_generation.factory import BaseGenerator

# Setup logger
logger = logging.getLogger("InsightFlowGenerator")


class JourneySimulator(BaseGenerator):
    """
    Simulates the customer journey events across Marketing, Application, and Loan lifecycles
    for a provided set of registered users. All relationships are configuration-driven.
    """
    def __init__(self, config: AppConfig):
        """
        Initializes the simulator with the configuration layer.

        Args:
            config (AppConfig): Shared validated application configuration.
        """
        super().__init__(config)
        
        # State tracking counters for event IDs
        self._mkt_counter = 1
        self._app_counter = 1
        self._lon_counter = 1

    def _get_loan_approval_probability(self, cibil_score: int) -> float:
        """
        Derives loan approval probability skewed by the user's CIBIL score.
        """
        rates = self.config.CIBIL_APPROVAL_RATES
        
        # Default rates if missing in config mapping
        ntc_rate = rates.get("ntc", 0.55)
        poor_rate = rates.get("poor", 0.10)
        fair_rate = rates.get("fair", 0.35)
        good_rate = rates.get("good", 0.70)
        excellent_rate = rates.get("excellent", 0.95)

        if cibil_score == -1:
            return ntc_rate
        elif cibil_score < 550:
            return poor_rate
        elif cibil_score < 650:
            return fair_rate
        elif cibil_score < 750:
            return good_rate
        else:
            return excellent_rate

    def simulate_marketing_stage(
        self, 
        user_id: str, 
        device: str, 
        state: str, 
        channel: str, 
        base_app_open_time: pd.Timestamp, 
        rng: np.random.Generator
    ) -> List[Dict[str, Any]]:
        """
        Simulates the marketing stage events (Impression, Click, Install) preceding app open.
        """
        # Time backtrack delays
        install_time = base_app_open_time - pd.to_timedelta(int(rng.integers(60, 600)), unit="s")
        click_time = install_time - pd.to_timedelta(int(rng.integers(120, 1800)), unit="s")
        impression_time = click_time - pd.to_timedelta(int(rng.integers(300, 86400)), unit="s")

        # Map channel to campaign and ad group names
        campaign_map = {
            "Google Ads": "Google_Search_Branded",
            "Meta Ads": "Meta_Feed_Prospecting",
            "Affiliate": "Affiliate_Referral_Offer",
            "Referral": "Referral_Program_V2",
            "Organic": "Organic_SEO_Direct"
        }
        campaign = campaign_map.get(channel, f"{channel}_Generic_Campaign")
        
        ad_groups = ["High_Intent_Broad", "Lookalike_Existing_Users", "Demographic_Target_GenZ", "Behavioral_Finance_Interests"]
        ad_group = f"{channel}_{rng.choice(ad_groups)}"

        # Simulated CPC and CPM costs in INR
        cost_impression = float(rng.uniform(0.0015, 0.005))  # $1.50 to $5.00 CPM -> cost per impression
        cost_click = float(rng.uniform(5.0, 40.0))            # Cost per click
        cost_install = 0.0

        marketing_events = []
        
        # 1. Impression
        marketing_events.append({
            "event_id": f"mkt_{self._mkt_counter:07d}",
            "user_id": user_id,
            "campaign": campaign,
            "channel": channel,
            "ad_group": ad_group,
            "device": device,
            "state": state,
            "cost": cost_impression,
            "timestamp": impression_time.strftime("%Y-%m-%d %H:%M:%S")
        })
        self._mkt_counter += 1

        # 2. Click
        marketing_events.append({
            "event_id": f"mkt_{self._mkt_counter:07d}",
            "user_id": user_id,
            "campaign": campaign,
            "channel": channel,
            "ad_group": ad_group,
            "device": device,
            "state": state,
            "cost": cost_click,
            "timestamp": click_time.strftime("%Y-%m-%d %H:%M:%S")
        })
        self._mkt_counter += 1

        # 3. Install
        marketing_events.append({
            "event_id": f"mkt_{self._mkt_counter:07d}",
            "user_id": user_id,
            "campaign": campaign,
            "channel": channel,
            "ad_group": ad_group,
            "device": device,
            "state": state,
            "cost": cost_install,
            "timestamp": install_time.strftime("%Y-%m-%d %H:%M:%S")
        })
        self._mkt_counter += 1

        return marketing_events

    def simulate_verification_stage(
        self, 
        user_id: str, 
        device: str, 
        otp_time: pd.Timestamp, 
        rng: np.random.Generator
    ) -> Tuple[List[Dict[str, Any]], pd.Timestamp]:
        """
        Simulates the application & verification stage events (App Open, Signup, OTP, KYC steps, Loan Apply).
        """
        rates = self.config.FUNNEL_CONVERSION_RATES
        
        # Platform derivation
        if "Android" in device:
            platform = "Android"
        elif "iOS" in device:
            platform = "iOS"
        else:
            platform = "Web"

        # Backtrack Signup and App Open times
        signup_time = otp_time - pd.to_timedelta(int(rng.integers(30, 180)), unit="s")
        app_open_time = signup_time - pd.to_timedelta(int(rng.integers(15, 120)), unit="s")

        app_events = []

        # Generate unique session IDs
        session_id_1 = f"ses_{rng.integers(1000000, 9999999)}"
        session_id_2 = f"ses_{rng.integers(1000000, 9999999)}"

        # 1. App Open
        app_events.append({
            "event_id": f"app_{self._app_counter:07d}",
            "user_id": user_id,
            "session_id": session_id_1,
            "platform": platform,
            "event_name": "App Open",
            "timestamp": app_open_time.strftime("%Y-%m-%d %H:%M:%S")
        })
        self._app_counter += 1

        # 2. Signup
        app_events.append({
            "event_id": f"app_{self._app_counter:07d}",
            "user_id": user_id,
            "session_id": session_id_1,
            "platform": platform,
            "event_name": "Signup",
            "timestamp": signup_time.strftime("%Y-%m-%d %H:%M:%S")
        })
        self._app_counter += 1

        # 3. OTP Verification
        app_events.append({
            "event_id": f"app_{self._app_counter:07d}",
            "user_id": user_id,
            "session_id": session_id_1,
            "platform": platform,
            "event_name": "OTP Verification",
            "timestamp": otp_time.strftime("%Y-%m-%d %H:%M:%S")
        })
        self._app_counter += 1

        last_time = otp_time

        # KYC Start
        if rng.random() > rates.get("otp_to_kyc_start", 0.85):
            return app_events, app_open_time

        kyc_start_time = last_time + pd.to_timedelta(int(rng.integers(30, 300)), unit="s")
        app_events.append({
            "event_id": f"app_{self._app_counter:07d}",
            "user_id": user_id,
            "session_id": session_id_1,
            "platform": platform,
            "event_name": "KYC Start",
            "timestamp": kyc_start_time.strftime("%Y-%m-%d %H:%M:%S")
        })
        self._app_counter += 1
        last_time = kyc_start_time

        # Face Match
        if rng.random() > rates.get("kyc_start_to_face_match", 0.95):
            return app_events, app_open_time

        face_match_time = last_time + pd.to_timedelta(int(rng.integers(20, 120)), unit="s")
        app_events.append({
            "event_id": f"app_{self._app_counter:07d}",
            "user_id": user_id,
            "session_id": session_id_1,
            "platform": platform,
            "event_name": "Face Match",
            "timestamp": face_match_time.strftime("%Y-%m-%d %H:%M:%S")
        })
        self._app_counter += 1
        last_time = face_match_time

        # PAN Verification
        if rng.random() > rates.get("face_match_to_pan_verify", 0.95):
            return app_events, app_open_time

        pan_verify_time = last_time + pd.to_timedelta(int(rng.integers(20, 120)), unit="s")
        app_events.append({
            "event_id": f"app_{self._app_counter:07d}",
            "user_id": user_id,
            "session_id": session_id_1,
            "platform": platform,
            "event_name": "PAN Verification",
            "timestamp": pan_verify_time.strftime("%Y-%m-%d %H:%M:%S")
        })
        self._app_counter += 1
        last_time = pan_verify_time

        # KYC Complete
        if rng.random() > rates.get("pan_verify_to_kyc_complete", 0.98):
            return app_events, app_open_time

        kyc_complete_time = last_time + pd.to_timedelta(int(rng.integers(15, 90)), unit="s")
        app_events.append({
            "event_id": f"app_{self._app_counter:07d}",
            "user_id": user_id,
            "session_id": session_id_1,
            "platform": platform,
            "event_name": "KYC Complete",
            "timestamp": kyc_complete_time.strftime("%Y-%m-%d %H:%M:%S")
        })
        self._app_counter += 1
        last_time = kyc_complete_time

        # Loan Apply (usually starts a new session if delay is long)
        if rng.random() > rates.get("kyc_complete_to_loan_apply", 0.75):
            return app_events, app_open_time

        apply_delay = int(rng.integers(60, 86400 * 3))
        session_to_use = session_id_1 if apply_delay < 1800 else session_id_2

        loan_apply_time = last_time + pd.to_timedelta(apply_delay, unit="s")
        app_events.append({
            "event_id": f"app_{self._app_counter:07d}",
            "user_id": user_id,
            "session_id": session_to_use,
            "platform": platform,
            "event_name": "Loan Apply",
            "timestamp": loan_apply_time.strftime("%Y-%m-%d %H:%M:%S")
        })
        self._app_counter += 1

        return app_events, app_open_time

    def simulate_loan_stage(
        self, 
        user_id: str, 
        cibil_score: int, 
        monthly_income: int, 
        apply_time: pd.Timestamp, 
        rng: np.random.Generator
    ) -> List[Dict[str, Any]]:
        """
        Simulates the loan decision and disbursement stage events.
        """
        rates = self.config.FUNNEL_CONVERSION_RATES
        loan_events = []

        # 1. Under Review
        under_review_time = apply_time + pd.to_timedelta(int(rng.integers(5, 60)), unit="s")
        loan_events.append({
            "event_id": f"lon_{self._lon_counter:07d}",
            "user_id": user_id,
            "loan_amount": 0,
            "approval_status": "Pending",
            "rejection_reason": "",
            "interest_rate": 0.0,
            "timestamp": under_review_time.strftime("%Y-%m-%d %H:%M:%S")
        })
        self._lon_counter += 1
        last_time = under_review_time

        # Generate Loan Amount based on income: median 3x income
        loan_amount = int(monthly_income * rng.uniform(1.5, 4.5))
        # Round to nearest 5,000 and clip
        loan_amount = max(10000, min(500000, (loan_amount // 5000) * 5000))

        # Interest rate assignment based on credit rating
        if cibil_score >= 750:
            interest_rate = round(float(rng.uniform(11.5, 14.5)), 2)
        elif cibil_score >= 650:
            interest_rate = round(float(rng.uniform(14.5, 18.0)), 2)
        elif cibil_score >= 550:
            interest_rate = round(float(rng.uniform(18.0, 22.0)), 2)
        elif cibil_score == -1:
            interest_rate = round(float(rng.uniform(15.0, 19.5)), 2)
        else:
            interest_rate = round(float(rng.uniform(22.0, 28.0)), 2)

        # Decide Loan Approval
        approval_prob = self._get_loan_approval_probability(cibil_score)
        is_approved = rng.random() <= approval_prob

        # Set delay: high CIBIL gets fast auto-approval, low gets manual review
        if cibil_score >= 750:
            decision_delay = int(rng.integers(30, 300))  # 30s to 5m
        else:
            decision_delay = int(rng.integers(1800, 86400))  # 30m to 24h

        decision_time = last_time + pd.to_timedelta(decision_delay, unit="s")

        if is_approved:
            loan_events.append({
                "event_id": f"lon_{self._lon_counter:07d}",
                "user_id": user_id,
                "loan_amount": loan_amount,
                "approval_status": "Approved",
                "rejection_reason": "",
                "interest_rate": interest_rate,
                "timestamp": decision_time.strftime("%Y-%m-%d %H:%M:%S")
            })
            self._lon_counter += 1
            last_time = decision_time

            # Disbursement Event
            if rng.random() <= rates.get("approved_to_disbursed", 0.90):
                disburse_delay = int(rng.integers(600, 86400 * 2))  # 10m to 2 days
                disbursed_time = last_time + pd.to_timedelta(disburse_delay, unit="s")
                loan_events.append({
                    "event_id": f"lon_{self._lon_counter:07d}",
                    "user_id": user_id,
                    "loan_amount": loan_amount,
                    "approval_status": "Disbursed",
                    "rejection_reason": "",
                    "interest_rate": interest_rate,
                    "timestamp": disbursed_time.strftime("%Y-%m-%d %H:%M:%S")
                })
                self._lon_counter += 1

        else:
            # Rejection Reasons based on constraints
            if cibil_score < 550 and cibil_score != -1:
                rejection_reason = "Low CIBIL Score"
            elif cibil_score == -1 and rng.random() < 0.40:
                rejection_reason = "Inadequate Credit History"
            elif monthly_income < 20000:
                rejection_reason = "Inadequate Monthly Income"
            else:
                rejection_reason = rng.choice([
                    "High Debt-to-Income Ratio",
                    "Verification Mismatch",
                    "Risk Profile Policy Exclusion"
                ])

            loan_events.append({
                "event_id": f"lon_{self._lon_counter:07d}",
                "user_id": user_id,
                "loan_amount": loan_amount,
                "approval_status": "Rejected",
                "rejection_reason": rejection_reason,
                "interest_rate": 0.0,
                "timestamp": decision_time.strftime("%Y-%m-%d %H:%M:%S")
            })
            self._lon_counter += 1

        return loan_events

    def validate_journey(self, combined_events: List[Dict[str, Any]]) -> bool:
        """
        Validates both chronological timestamp progression and logical business state transitions.

        Args:
            combined_events (List[Dict]): Combined sorted event dictionaries for a user.

        Returns:
            bool: True if validation passes, otherwise False.
        """
        if not combined_events:
            return True

        # 1. Chronological order check
        for i in range(1, len(combined_events)):
            t_prev = combined_events[i-1]["timestamp"]
            t_curr = combined_events[i]["timestamp"]
            if t_curr < t_prev:
                logger.error(
                    f"Chronological Validation Error: Event {combined_events[i]['event_type' if 'event_type' in combined_events[i] else 'event_name']} ({combined_events[i]['timestamp']}) "
                    f"occurs before {combined_events[i-1]['event_type' if 'event_type' in combined_events[i-1] else 'event_name']} ({combined_events[i-1]['timestamp']}) "
                    f"for user {combined_events[i]['user_id']}"
                )
                return False

        # Extract sequence of events
        event_names = []
        for evt in combined_events:
            if "event_type" in evt:
                event_names.append(evt["event_type"])
            elif "event_name" in evt:
                event_names.append(evt["event_name"])

        # 2. Business Transition Checks
        # - Disbursed -> Rejected must never occur
        if "Disbursed" in event_names and "Rejected" in event_names:
            logger.error("Business Transition Error: Disbursed followed by Rejection.")
            return False

        # - Disbursed without Approved must never occur
        if "Disbursed" in event_names and "Approved" not in event_names:
            logger.error("Business Transition Error: Disbursed occurred without Approved decision.")
            return False

        # - Loan Applied -> Signup must never occur (Signup occurs first)
        if "Loan Apply" in event_names and "Signup" in event_names:
            signup_idx = event_names.index("Signup")
            apply_idx = event_names.index("Loan Apply")
            if signup_idx > apply_idx:
                logger.error("Business Transition Error: Signup occurred after Loan Apply.")
                return False

        # - KYC complete cannot occur before Signup
        if "KYC Complete" in event_names and "Signup" in event_names:
            signup_idx = event_names.index("Signup")
            kyc_idx = event_names.index("KYC Complete")
            if signup_idx > kyc_idx:
                logger.error("Business Transition Error: Signup occurred after KYC Complete.")
                return False

        # Funnel stage precedence ordering
        funnel_precedence = [
            "Impression", "Click", "Install", "App Open", "Signup", "OTP Verification",
            "KYC Start", "Face Match", "PAN Verification", "KYC Complete", "Loan Apply",
            "Pending"  # Under Review is Pending
        ]

        last_funnel_idx = -1
        for name in event_names:
            if name in funnel_precedence:
                current_idx = funnel_precedence.index(name)
                if current_idx < last_funnel_idx:
                    logger.error(f"Business Funnel Sequence Error: Out-of-order transition {name} after an advanced stage.")
                    return False
                last_funnel_idx = current_idx
            
            elif name in ["Approved", "Rejected"]:
                if "Pending" not in event_names:
                    logger.error(f"Business Funnel Sequence Error: {name} occurred without Pending review.")
                    return False

            elif name == "Disbursed":
                if "Approved" not in event_names:
                    logger.error("Business Funnel Sequence Error: Disbursed occurred without Approved decision.")
                    return False

        return True

    def generate(
        self, 
        users_csv_path: str = "data/synthetic/users.csv",
        output_dir: str = "data/synthetic"
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Simulates stages for all users in the CSV file, validates ordering, and exports CSV datasets.

        Args:
            users_csv_path (str): Input path to users synthetic dataset.
            output_dir (str): Directory where simulated event logs are exported.

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: DataFrames of marketing, app, and loan events.

        Raises:
            FileNotFoundError: If users.csv is missing.
            ValueError: If chronological integrity constraints fail.
        """
        logger.info(f"Starting journey simulation E2E using input: {users_csv_path}")

        if not os.path.exists(users_csv_path):
            raise FileNotFoundError(f"Input users file not found at: {users_csv_path}")

        df_users = pd.read_csv(users_csv_path)
        logger.info(f"Loaded {len(df_users):,} users to simulate lifecycles.")

        # Local reproducible Random State generator
        rng = np.random.default_rng(self.config.SEED)

        all_marketing = []
        all_app = []
        all_loan = []

        # Reset global sequence counters
        self._mkt_counter = 1
        self._app_counter = 1
        self._lon_counter = 1

        for idx, row in df_users.iterrows():
            user_id = str(row["user_id"])
            device = str(row["device"])
            state = str(row["state"])
            channel = str(row["acquisition_channel"])
            cibil_score = int(row["cibil_score"])
            monthly_income = int(row["monthly_income"])
            reg_date_str = str(row["registration_date"])

            # 1. Base OTP Verification time randomly sampled between 08:00 AM and 08:00 PM on registration date
            base_date = pd.to_datetime(reg_date_str)
            otp_hour = int(rng.integers(8, 20))
            otp_minute = int(rng.integers(0, 60))
            otp_second = int(rng.integers(0, 60))
            otp_time = base_date + pd.to_timedelta(otp_hour, unit="h") + \
                       pd.to_timedelta(otp_minute, unit="m") + \
                       pd.to_timedelta(otp_second, unit="s")

            # 2. Simulate Application Verification Stage (including App Open timestamp)
            app_events, app_open_time = self.simulate_verification_stage(user_id, device, otp_time, rng)

            # 3. Simulate Marketing Stage using the App Open time
            marketing_events = self.simulate_marketing_stage(user_id, device, state, channel, app_open_time, rng)

            # 4. Simulate Loan Stage if the user applied for a loan
            loan_events = []
            has_applied = any(evt["event_name"] == "Loan Apply" for evt in app_events)
            if has_applied:
                apply_evt = [evt for evt in app_events if evt["event_name"] == "Loan Apply"][0]
                apply_time = pd.to_datetime(apply_evt["timestamp"])
                loan_events = self.simulate_loan_stage(user_id, cibil_score, monthly_income, apply_time, rng)

            # 5. Combine and validate chronological and state integrity
            combined_user_journey = []
            for evt in marketing_events:
                combined_user_journey.append(dict(evt))
            for evt in app_events:
                # normalize field name for sort validation
                norm_evt = dict(evt)
                norm_evt["event_type"] = norm_evt["event_name"]
                combined_user_journey.append(norm_evt)
            for evt in loan_events:
                # normalize field name
                norm_evt = dict(evt)
                norm_evt["event_type"] = norm_evt["approval_status"]
                combined_user_journey.append(norm_evt)

            # Sort combined events chronologically (lexicographically for ISO string timestamps)
            combined_user_journey.sort(key=lambda x: x["timestamp"])

            if not self.validate_journey(combined_user_journey):
                error_msg = f"Journey validation failed at user index {idx+1} (user_id: {user_id})."
                logger.error(error_msg)
                raise ValueError(error_msg)

            all_marketing.extend(marketing_events)
            all_app.extend(app_events)
            all_loan.extend(loan_events)

            if (idx + 1) % max(1, len(df_users) // 10) == 0 or (idx + 1) == len(df_users):
                logger.info(f"Simulated lifecycle journeys for {idx+1:,} / {len(df_users):,} users...")

        # Convert to DataFrames
        df_marketing = pd.DataFrame(all_marketing)
        df_app = pd.DataFrame(all_app)
        df_loan = pd.DataFrame(all_loan)

        # Enforce output directories exist
        os.makedirs(output_dir, exist_ok=True)

        mkt_path = os.path.join(output_dir, "marketing_events.csv")
        app_path = os.path.join(output_dir, "app_events.csv")
        lon_path = os.path.join(output_dir, "loan_events.csv")

        # Export DataFrames to CSV
        df_marketing.to_csv(mkt_path, index=False)
        df_app.to_csv(app_path, index=False)
        df_loan.to_csv(lon_path, index=False)

        logger.info(f"Successfully simulated and exported lifecycle event logs to: {output_dir}")
        logger.info(f"Marketing Events: {len(df_marketing):,} rows")
        logger.info(f"Application Events: {len(df_app):,} rows")
        logger.info(f"Loan Events: {len(df_loan):,} rows")

        return df_marketing, df_app, df_loan


def main():
    """Main execution block to run Journey Simulator standalone."""
    parser = argparse.ArgumentParser(description="InsightFlow Customer Journey Lifecycle Simulator")
    parser.add_argument(
        "--config", 
        type=str, 
        default="config/settings.yaml", 
        help="Path to configuration settings YAML file"
    )
    parser.add_argument(
        "--users", 
        type=str, 
        default="data/synthetic/users.csv", 
        help="Path to users input CSV file"
    )
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="data/synthetic", 
        help="Directory to save simulated event logs"
    )
    args = parser.parse_args()

    # Load configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"CRITICAL: Failed to load config from {args.config}: {e}", file=sys.stderr)
        sys.exit(1)

    # Initialize Simulator
    simulator = JourneySimulator(config)
    
    try:
        simulator.generate(args.users, args.output_dir)
        print("Journey Simulation completed successfully!")
    except Exception as e:
        logger.exception(f"Journey simulation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
