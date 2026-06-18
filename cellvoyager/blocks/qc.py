from __future__ import annotations

from typing import Any

import scanpy as sc


def qc_summary(
    adata: Any,
    groupby: list[str] | None = None,
    apply_filters: bool = False,
    min_genes: int = 200,
    min_counts: int = 500,
    max_counts: int = 50000,
    max_mito_pct: float = None,
    min_cell_per_gene: int = 3,
) -> tuple[Any, dict]:
    """
    This CellVoyager block is a template for QC on an AnnData object:

    Parameters:
        adata: AnnData object to perform QC on.
        groupby: List of columns in adata.obs to group by for QC summary.
        apply_filters: Whether to apply filtering based on QC metrics.
        min_genes: Minimum number of genes per cell.
        min_counts: Minimum number of counts per cell.
        max_counts: Maximum number of counts per cell.
        max_mito_pct: Maximum percentage of mitochondrial genes per cell.
        min_cell_per_gene: Minimum number of cells expressing a gene.

    Runs:
        1. Detects mitochondrial genes and calculates QC metrics.
        2. Calculate QC metrics.
        3. Generate a QC summary grouped by specified columns.
        4. Optionally apply filtering based on QC metrics.
    """

    if groupby is None:
        groupby = []

    cells_before_filtering = adata.n_obs
    genes_before_filtering = adata.n_vars

    warnings = []

    # Annotate the mt genes in the AnnData obj
    adata.var["mt"] = adata.var_names.str.upper().str.startswith("MT-")

    try:
        n_mt_genes = int(adata.var["mt"].sum())
        if n_mt_genes == 0:
            warnings.append(
                "No mitochondrial genes detected. QC metrics may be inaccurate."
            )

    except Exception:
        warnings.append("Could not determine the number of mitochondrial genes.")

    # Calculate QC metrics
    required_qc_metrics = ["n_genes_by_counts", "total_counts", "pct_counts_mt"]
    missing_metrics = [
        metric for metric in required_qc_metrics if metric not in adata.obs.columns
    ]

    if missing_metrics and adata.var["mt"].any():
        sc.pp.calculate_qc_metrics(
            adata,
            qc_vars=["mt"],
            percent_top=None,
            log1p=False,
            inplace=True,
        )

    else:
        warnings.append(
            f"Missing QC metrics: {', '.join(missing_metrics)}. QC summary may be incomplete."
        )

    missing_after = [
        metric for metric in required_qc_metrics if metric not in adata.obs.columns
    ]
    if missing_after:
        return adata, {
            "status": "failed",
            "message": f"QC metrics calculation failed. Missing metrics: {', '.join(missing_after)}.",
            "warnings": warnings,
            "results": {},
        }

    # Generate QC summary
    def make_summary(obs: Any) -> dict[str, float]:
        return {
            "n_cells": obs.shape[0],
            "mean_n_genes": float(obs["n_genes_by_counts"].mean()),
            "median_n_genes": float(obs["n_genes_by_counts"].median()),
            "mean_total_counts": float(obs["total_counts"].mean()),
            "median_total_counts": float(obs["total_counts"].median()),
            "mean_pct_mito": float(obs["pct_counts_mt"].mean()),
            "median_pct_mito": float(obs["pct_counts_mt"].median()),
        }

    results = {}

    # Small funtion inside the list that only includes groupby columns that are actually present in adata.obs
    available_groupby = [col for col in groupby if col in adata.obs.columns]
    missing_groupby = [col for col in groupby if col not in adata.obs.columns]

    if missing_groupby:
        warnings.append(
            f"Some groupby columns are missing in adata.obs: {', '.join(missing_groupby)}."
        )

    if available_groupby:
        grouped = adata.obs.groupby(available_groupby, observed=True)
        for group_name, group_data in grouped:
            if isinstance(group_name, tuple):
                group_name = " | ".join(map(str, group_name))
            else:
                group_name = str(group_name)

            results[group_name] = make_summary(group_data)

    else:
        results["overall"] = make_summary(adata.obs)

    # Filtering
    filter_applied = False

    if apply_filters:
        sc.pp.filter_cells(adata, min_genes=min_genes)
        sc.pp.filter_cells(adata, min_counts=min_counts)
        sc.pp.filter_cells(adata, max_counts=max_counts)

        if max_mito_pct is not None:
            if "pct_counts_mt" in adata.obs.columns:
                adata = adata[adata.obs["pct_counts_mt"] <= max_mito_pct].copy()
            else:
                warnings.append(
                    "pct_counts_mt not found, so mitochondrial filtering was skipped."
                )
        else:
            warnings.append(
                "No max_mito_pct supplied, so mitochondrial filtering was skipped."
            )

        sc.pp.filter_genes(adata, min_cells=min_cell_per_gene)

        filter_applied = True

        cells_after_filtering = adata.n_obs
        genes_after_filtering = adata.n_vars

    # Summary
    overall_summary = make_summary(adata.obs)

    summary_text = (
        f"QC Summary:\n"
        f"Mitochondrial genes detected: {n_mt_genes}\n"
        f"Cells before filtering: {cells_before_filtering}\n"
        f"Genes before filtering: {genes_before_filtering}\n"
        f"Median genes per cell: {overall_summary['median_n_genes']:.2f}\n"
        f"Median counts per cell: {overall_summary['median_total_counts']:.2f}\n"
        f"Median mitochondrial percentage: {overall_summary['median_pct_mito']:.2f}\n"
    )

    if filter_applied:
        summary_text += (
            f"Cells after filtering: {cells_after_filtering}\n"
            f"Genes after filtering: {genes_after_filtering}\n"
        )

    else:
        summary_text += "No filtering applied.\n"

    result = {
        "status": "success" if not warnings else "partial",
        "message": summary_text,
        "warnings": warnings,
        "results": results,
        "filter_applied": filter_applied,
    }

    return adata, result
