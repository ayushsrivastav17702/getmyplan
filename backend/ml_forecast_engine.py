"""
AI/ML Demand Forecasting Engine
Models: Holt-Winters, Random Forest, Seasonal Decomposition, Ensemble
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import warnings
import logging

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    from statsmodels.tsa.seasonal import seasonal_decompose
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logger.warning("statsmodels not available – some forecasting features disabled.")


class MLForecastEngine:
    """Ensemble AI Demand Forecasting Engine"""

    # ── MODEL 1: Holt-Winters ──────────────────────────────────

    def holt_winters_forecast(
        self, data: List[float], seasonal_periods: int = 12, forecast_horizon: int = 12
    ) -> Optional[Dict]:
        if not STATSMODELS_AVAILABLE or len(data) < seasonal_periods * 2:
            return None
        try:
            model = ExponentialSmoothing(
                data,
                seasonal_periods=seasonal_periods,
                trend='add',
                seasonal='add',
                initialization_method='estimated',
            )
            fitted = model.fit(optimized=True)
            forecast = fitted.forecast(forecast_horizon)
            residuals = fitted.resid
            std_resid = float(np.std(residuals)) if len(residuals) > 0 else float(np.std(data)) * 0.1

            acc = {}
            if len(data) >= 12:
                acc = self._accuracy(data[-12:], list(fitted.fittedvalues[-12:]))

            return {
                'forecast': [round(max(0, float(v)), 2) for v in forecast],
                'lower_bound': [round(max(0, float(v) - 1.96 * std_resid), 2) for v in forecast],
                'upper_bound': [round(float(v) + 1.96 * std_resid, 2) for v in forecast],
                'model': 'Holt-Winters',
                'accuracy': acc,
            }
        except Exception as e:
            logger.warning("Holt-Winters failed: %s", e)
            return None

    # ── MODEL 2: Random Forest ─────────────────────────────────

    def random_forest_forecast(
        self, data: List[float], forecast_horizon: int = 12
    ) -> Optional[Dict]:
        if len(data) < 24:
            return None
        try:
            df = pd.DataFrame({'value': data})
            for lag in [1, 2, 3, 6, 12]:
                df[f'lag_{lag}'] = df['value'].shift(lag)
            df['rolling_mean_3'] = df['value'].rolling(3).mean()
            df['rolling_mean_6'] = df['value'].rolling(6).mean()
            df['rolling_std_3'] = df['value'].rolling(3).std()
            df['month'] = [i % 12 for i in range(len(df))]
            df['quarter'] = [i // 3 % 4 for i in range(len(df))]
            df = df.dropna()

            if len(df) < 12:
                return None

            feature_cols = [c for c in df.columns if c != 'value']
            X = df[feature_cols].values
            y = df['value'].values

            split = int(len(X) * 0.8)
            X_train, X_val = X[:split], X[split:]
            y_train, y_val = y[:split], y[split:]

            model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=1)
            model.fit(X_train, y_train)

            # recursive prediction
            predictions = []
            last_values = list(data)
            for i in range(forecast_horizon):
                features = []
                for lag in [1, 2, 3, 6, 12]:
                    features.append(last_values[-lag] if len(last_values) >= lag else 0)
                features.append(float(np.mean(last_values[-3:])) if len(last_values) >= 3 else 0)
                features.append(float(np.mean(last_values[-6:])) if len(last_values) >= 6 else 0)
                features.append(float(np.std(last_values[-3:])) if len(last_values) >= 3 else 0)
                features.append((len(last_values) + i) % 12)
                features.append(((len(last_values) + i) // 3) % 4)
                pred = float(model.predict([features])[0])
                predictions.append(round(max(0, pred), 2))
                last_values.append(pred)

            y_pred_val = model.predict(X_val)
            acc = self._accuracy(list(y_val), list(y_pred_val)) if len(y_val) > 0 else {}

            return {
                'forecast': predictions,
                'model': 'Random Forest',
                'accuracy': acc,
            }
        except Exception as e:
            logger.warning("Random Forest failed: %s", e)
            return None

    # ── MODEL 3: Seasonal Decomposition ────────────────────────

    def seasonal_decomposition_forecast(
        self, data: List[float], seasonal_periods: int = 12, forecast_horizon: int = 12
    ) -> Optional[Dict]:
        if not STATSMODELS_AVAILABLE or len(data) < seasonal_periods * 2:
            return None
        try:
            decomp = seasonal_decompose(data, model='additive', period=seasonal_periods, extrapolate_trend='freq')
            trend = decomp.trend.values
            seasonal = decomp.seasonal.values[-seasonal_periods:]

            valid_trend = trend[~np.isnan(trend)]
            if len(valid_trend) > 3:
                lr = LinearRegression()
                lr.fit(np.arange(len(valid_trend)).reshape(-1, 1), valid_trend)
                future_trend = lr.predict(
                    np.arange(len(valid_trend), len(valid_trend) + forecast_horizon).reshape(-1, 1)
                )
            else:
                future_trend = np.full(forecast_horizon, np.mean(data))

            forecast = []
            for i in range(forecast_horizon):
                pred = float(future_trend[i]) + float(seasonal[i % seasonal_periods])
                forecast.append(round(max(0, pred), 2))

            return {
                'forecast': forecast,
                'model': 'Seasonal Decomposition',
                'accuracy': {},
            }
        except Exception as e:
            logger.warning("Seasonal Decomposition failed: %s", e)
            return None

    # ── ENSEMBLE ───────────────────────────────────────────────

    def ensemble_forecast(
        self, data: List[float], seasonal_periods: int = 12, forecast_horizon: int = 12
    ) -> Dict:
        models_results = []

        hw = self.holt_winters_forecast(data, seasonal_periods, forecast_horizon)
        if hw:
            models_results.append(hw)
        rf = self.random_forest_forecast(data, forecast_horizon)
        if rf:
            models_results.append(rf)
        sd = self.seasonal_decomposition_forecast(data, seasonal_periods, forecast_horizon)
        if sd:
            models_results.append(sd)

        if not models_results:
            ma = float(np.mean(data[-12:])) if len(data) >= 12 else (float(np.mean(data)) if data else 0)
            return {
                'forecast': [round(ma, 2)] * forecast_horizon,
                'models_used': ['Moving Average (Fallback)'],
                'individual_forecasts': {},
                'confidence_intervals': {'lower': [round(ma * 0.8, 2)] * forecast_horizon,
                                         'upper': [round(ma * 1.2, 2)] * forecast_horizon},
                'ensemble_accuracy': {'confidence_score': 50},
            }

        n = len(models_results)
        ensemble = []
        for i in range(forecast_horizon):
            val = sum(m['forecast'][i] for m in models_results) / n
            ensemble.append(round(val, 2))

        matrix = np.array([m['forecast'] for m in models_results])
        pred_std = np.std(matrix, axis=0)
        avg_f = float(np.mean(ensemble)) if ensemble else 1
        confidence = max(50, min(95, 100 - (float(np.mean(pred_std)) / avg_f * 100))) if avg_f > 0 else 50

        lower = [round(max(0, ensemble[i] - 1.96 * float(pred_std[i])), 2) for i in range(forecast_horizon)]
        upper = [round(ensemble[i] + 1.96 * float(pred_std[i]), 2) for i in range(forecast_horizon)]

        return {
            'forecast': ensemble,
            'models_used': [m['model'] for m in models_results],
            'individual_forecasts': {m['model']: m['forecast'] for m in models_results},
            'confidence_intervals': {'lower': lower, 'upper': upper},
            'ensemble_accuracy': {'confidence_score': round(confidence, 1)},
        }

    # ── helpers ─────────────────────────────────────────────────

    @staticmethod
    def _accuracy(actual: list, predicted: list) -> Dict:
        if not actual or not predicted or len(actual) != len(predicted):
            return {}
        a = np.array(actual, dtype=float)
        p = np.array(predicted, dtype=float)
        mape = float(np.mean(np.abs((a - p) / np.where(a == 0, 1, a)))) * 100
        rmse = float(np.sqrt(mean_squared_error(a, p)))
        r2 = float(r2_score(a, p)) if len(a) > 1 else 0
        return {'mape': round(mape, 1), 'rmse': round(rmse, 2), 'r2': round(r2, 3)}
