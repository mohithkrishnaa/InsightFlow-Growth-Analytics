CREATE INDEX idx_users_state ON users(state);
CREATE INDEX idx_users_city ON users(city);
CREATE INDEX idx_users_channel ON users(acquisition_channel);

CREATE INDEX idx_marketing_user ON marketing_events(user_id);
CREATE INDEX idx_marketing_channel ON marketing_events(channel);

CREATE INDEX idx_app_user ON app_events(user_id);
CREATE INDEX idx_app_event ON app_events(event_name);

CREATE INDEX idx_loan_user ON loan_events(user_id);
CREATE INDEX idx_loan_status ON loan_events(approval_status);

CREATE INDEX idx_experiment_user ON experiments(user_id);
CREATE INDEX idx_experiment_name ON experiments(experiment_name);