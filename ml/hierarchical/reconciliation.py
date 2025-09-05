from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from enum import Enum


class ReconciliationMethod(str, Enum):
    TOP_DOWN = "top_down"
    BOTTOM_UP = "bottom_up"
    MIDDLE_OUT = "middle_out"
    MINT = "mint"  # Minimum Trace reconciliation


class HierarchicalReconciler:
    """Hierarchical forecasting reconciliation methods."""
    
    def __init__(self, hierarchy: Dict[str, List[str]]):
        """
        Initialize with hierarchy structure.
        
        Args:
            hierarchy: Dict mapping parent nodes to their children
                      e.g., {"Brand": ["SKU1", "SKU2"], "Geo": ["US", "CA"]}
        """
        self.hierarchy = hierarchy
        self.levels = self._build_levels()
    
    def _build_levels(self) -> List[List[str]]:
        """Build hierarchy levels from bottom to top."""
        all_nodes = set()
        for children in self.hierarchy.values():
            all_nodes.update(children)
        
        # Find root nodes (not children of any parent)
        root_nodes = set(self.hierarchy.keys()) - all_nodes
        
        levels = []
        current_level = list(root_nodes)
        
        while current_level:
            levels.append(current_level)
            next_level = []
            for node in current_level:
                if node in self.hierarchy:
                    next_level.extend(self.hierarchy[node])
            current_level = next_level
        
        return levels
    
    def top_down_reconcile(
        self,
        forecasts: Dict[str, np.ndarray],
        proportions: Dict[str, np.ndarray],
        method: str = "average"
    ) -> Dict[str, np.ndarray]:
        """
        Top-down reconciliation.
        
        Args:
            forecasts: Dict of node forecasts
            proportions: Dict of historical proportions for each child
            method: Method to calculate proportions ("average", "last", "seasonal")
        
        Returns:
            Dict of reconciled forecasts
        """
        reconciled = {}
        
        for level in self.levels:
            for parent in level:
                if parent in forecasts and parent in self.hierarchy:
                    parent_forecast = forecasts[parent]
                    children = self.hierarchy[parent]
                    
                    # Calculate proportions
                    if method == "average":
                        proportions_avg = np.mean([proportions[child] for child in children], axis=0)
                    elif method == "last":
                        proportions_avg = np.array([proportions[child][-1] for child in children])
                    else:  # seasonal
                        proportions_avg = np.mean([proportions[child] for child in children], axis=0)
                    
                    # Normalize proportions
                    proportions_avg = proportions_avg / np.sum(proportions_avg)
                    
                    # Distribute parent forecast to children
                    for i, child in enumerate(children):
                        if child in forecasts:
                            reconciled[child] = parent_forecast * proportions_avg[i]
                        else:
                            reconciled[child] = parent_forecast * proportions_avg[i]
        
        return reconciled
    
    def bottom_up_reconcile(
        self,
        forecasts: Dict[str, np.ndarray]
    ) -> Dict[str, np.ndarray]:
        """
        Bottom-up reconciliation.
        
        Args:
            forecasts: Dict of node forecasts
        
        Returns:
            Dict of reconciled forecasts
        """
        reconciled = forecasts.copy()
        
        # Start from bottom level and aggregate up
        for level in reversed(self.levels):
            for parent in level:
                if parent in self.hierarchy:
                    children = self.hierarchy[parent]
                    child_forecasts = [reconciled[child] for child in children if child in reconciled]
                    
                    if child_forecasts:
                        # Sum child forecasts to get parent
                        reconciled[parent] = np.sum(child_forecasts, axis=0)
        
        return reconciled
    
    def middle_out_reconcile(
        self,
        forecasts: Dict[str, np.ndarray],
        middle_level: str,
        proportions: Dict[str, np.ndarray]
    ) -> Dict[str, np.ndarray]:
        """
        Middle-out reconciliation.
        
        Args:
            forecasts: Dict of node forecasts
            middle_level: The middle level node to start from
            proportions: Dict of historical proportions
        
        Returns:
            Dict of reconciled forecasts
        """
        reconciled = forecasts.copy()
        
        # First, do bottom-up from middle level
        if middle_level in self.hierarchy:
            children = self.hierarchy[middle_level]
            child_forecasts = [reconciled[child] for child in children if child in reconciled]
            
            if child_forecasts:
                reconciled[middle_level] = np.sum(child_forecasts, axis=0)
        
        # Then do top-down from middle level
        reconciled = self.top_down_reconcile(reconciled, proportions)
        
        return reconciled
    
    def mint_reconcile(
        self,
        forecasts: Dict[str, np.ndarray],
        errors: Dict[str, np.ndarray],
        method: str = "ols"
    ) -> Dict[str, np.ndarray]:
        """
        Minimum Trace (MinT) reconciliation.
        
        Args:
            forecasts: Dict of node forecasts
            errors: Dict of historical forecast errors
            method: Reconciliation method ("ols", "wls", "shr")
        
        Returns:
            Dict of reconciled forecasts
        """
        # This is a simplified implementation
        # In practice, you'd use a proper MinT implementation
        
        reconciled = forecasts.copy()
        
        # Calculate reconciliation weights based on error variances
        weights = {}
        for node, error in errors.items():
            if len(error) > 0:
                weights[node] = 1.0 / (np.var(error) + 1e-8)  # Add small constant for stability
            else:
                weights[node] = 1.0
        
        # Normalize weights
        total_weight = sum(weights.values())
        for node in weights:
            weights[node] /= total_weight
        
        # Apply weighted reconciliation
        for node in reconciled:
            if node in weights:
                # This is a simplified version - real MinT is more complex
                reconciled[node] = reconciled[node] * weights[node]
        
        return reconciled
    
    def reconcile_forecasts(
        self,
        forecasts: Dict[str, np.ndarray],
        method: ReconciliationMethod = ReconciliationMethod.BOTTOM_UP,
        **kwargs
    ) -> Dict[str, np.ndarray]:
        """
        Reconcile forecasts using specified method.
        
        Args:
            forecasts: Dict of node forecasts
            method: Reconciliation method
            **kwargs: Additional arguments for specific methods
        
        Returns:
            Dict of reconciled forecasts
        """
        if method == ReconciliationMethod.TOP_DOWN:
            return self.top_down_reconcile(forecasts, **kwargs)
        elif method == ReconciliationMethod.BOTTOM_UP:
            return self.bottom_up_reconcile(forecasts)
        elif method == ReconciliationMethod.MIDDLE_OUT:
            return self.middle_out_reconcile(forecasts, **kwargs)
        elif method == ReconciliationMethod.MINT:
            return self.mint_reconcile(forecasts, **kwargs)
        else:
            raise ValueError(f"Unknown reconciliation method: {method}")


def create_pharma_hierarchy() -> HierarchicalReconciler:
    """Create a pharma-specific hierarchy structure."""
    hierarchy = {
        "Total": ["Brand_A", "Brand_B", "Brand_C"],
        "Brand_A": ["Brand_A_US", "Brand_A_CA", "Brand_A_UK"],
        "Brand_B": ["Brand_B_US", "Brand_B_CA", "Brand_B_UK"],
        "Brand_C": ["Brand_C_US", "Brand_C_CA", "Brand_C_UK"],
        "Brand_A_US": ["Brand_A_US_Retail", "Brand_A_US_Hospital"],
        "Brand_A_CA": ["Brand_A_CA_Retail", "Brand_A_CA_Hospital"],
        "Brand_A_UK": ["Brand_A_UK_Retail", "Brand_A_UK_Hospital"],
    }
    
    return HierarchicalReconciler(hierarchy)


def calculate_forecast_accuracy(
    actual: Dict[str, np.ndarray],
    forecast: Dict[str, np.ndarray]
) -> Dict[str, float]:
    """Calculate forecast accuracy metrics for hierarchical forecasts."""
    metrics = {}
    
    for node in actual:
        if node in forecast:
            actual_vals = actual[node]
            forecast_vals = forecast[node]
            
            if len(actual_vals) == len(forecast_vals):
                mape = np.mean(np.abs((actual_vals - forecast_vals) / actual_vals)) * 100
                mae = np.mean(np.abs(actual_vals - forecast_vals))
                rmse = np.sqrt(np.mean((actual_vals - forecast_vals) ** 2))
                
                metrics[node] = {
                    "mape": mape,
                    "mae": mae,
                    "rmse": rmse
                }
    
    return metrics
