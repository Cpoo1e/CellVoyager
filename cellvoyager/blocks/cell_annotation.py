import numpy as np
import pandas as pd
import scanpy as sc


def annotate_clusters_summary(
    adata,
    cluster_key="leiden_r05",
    layer="X_log1p",
    out_key="cell_type",
    marker_genes=None,
    min_score=0.0,
    min_margin=0.05,
):
    """
    Annotate Leiden clusters by scoring canonical marker genes.

    Stores:
    - adata.obs[out_key]
    - adata.uns[f"{out_key}_score_table"]
    - adata.uns[f"{out_key}_cluster_table"]
    - adata.uns[f"{out_key}_markers_present"]
    """

    warnings = []

    if cluster_key not in adata.obs.columns:
        return adata, {
            "status": "failed",
            "message": f"Cluster key '{cluster_key}' not found in adata.obs.",
            "warnings": warnings,
            "results": {},
        }

    if marker_genes is None:
        return adata, {
            "status": "failed",
            "message": "No marker genes provided for annotation.",
            "warnings": warnings,
            "results": {},
        }

    # Keep only marker genes present in the dataset
    markers_present = {}
    markers_missing = {}

    for cell_type, genes in marker_genes.items():
        present = [gene for gene in genes if gene in adata.var_names]
        missing = [gene for gene in genes if gene not in adata.var_names]

        if present:
            markers_present[cell_type] = present

        markers_missing[cell_type] = missing

    if not markers_present:
        return adata, {
            "status": "failed",
            "message": "None of the marker genes were found in adata.var_names.",
            "warnings": warnings,
            "results": {},
        }

    # Score each cell for each marker-defined cell type
    score_cols = {}

    for cell_type, genes in markers_present.items():
        score_col = f"score_{cell_type}"
        score_cols[cell_type] = score_col

        try:
            sc.tl.score_genes(
                adata,
                gene_list=genes,
                score_name=score_col,
                use_raw=False,
                layer=layer if layer in adata.layers else None,
            )
        except TypeError:
            # Fallback for older Scanpy versions without layer= in score_genes
            if layer is not None and layer in adata.layers:
                old_X = adata.X
                adata.X = adata.layers[layer].copy()

                sc.tl.score_genes(
                    adata,
                    gene_list=genes,
                    score_name=score_col,
                    use_raw=False,
                )

                adata.X = old_X
            else:
                sc.tl.score_genes(
                    adata,
                    gene_list=genes,
                    score_name=score_col,
                    use_raw=False,
                )

    # Average marker scores per Leiden cluster
    score_table = adata.obs.groupby(cluster_key)[list(score_cols.values())].mean()

    # Rename columns from score_CD4_T_cells -> CD4_T_cells
    score_table.columns = [col.replace("score_", "") for col in score_table.columns]

    # Assign each cluster to the highest scoring cell type
    annotation_rows = []
    cluster_to_celltype = {}

    for cluster in score_table.index.astype(str):
        scores = score_table.loc[cluster].sort_values(ascending=False)

        top_label = scores.index[0]
        top_score = float(scores.iloc[0])

        second_label = scores.index[1] if len(scores) > 1 else None
        second_score = float(scores.iloc[1]) if len(scores) > 1 else np.nan
        margin = top_score - second_score if second_label is not None else np.nan

        if top_score < min_score or margin < min_margin:
            assigned = "Unassigned"
            confidence = "low"
        else:
            assigned = top_label
            confidence = "medium"

        cluster_to_celltype[cluster] = assigned

        annotation_rows.append(
            {
                "cluster": cluster,
                "assigned_cell_type": assigned,
                "confidence": confidence,
                "top_marker_match": top_label,
                "top_score": top_score,
                "second_marker_match": second_label,
                "second_score": second_score,
                "score_margin": margin,
                "n_cells": int((adata.obs[cluster_key].astype(str) == cluster).sum()),
            }
        )

    cluster_table = pd.DataFrame(annotation_rows)

    # Apply labels to every cell based on its Leiden cluster
    adata.obs[out_key] = (
        adata.obs[cluster_key].astype(str).map(cluster_to_celltype).astype("category")
    )

    # Store evidence for plotting/review
    adata.uns[f"{out_key}_score_table"] = score_table
    adata.uns[f"{out_key}_cluster_table"] = cluster_table
    adata.uns[f"{out_key}_markers_present"] = markers_present
    adata.uns[f"{out_key}_markers_missing"] = markers_missing

    cell_type_counts = {
        str(k): int(v) for k, v in adata.obs[out_key].value_counts().to_dict().items()
    }

    results = {
        "n_cells": int(adata.n_obs),
        "n_genes": int(adata.n_vars),
        "cluster_key": cluster_key,
        "out_key": out_key,
        "n_clusters": int(adata.obs[cluster_key].nunique()),
        "n_cell_types": int(adata.obs[out_key].nunique()),
        "cell_type_counts": cell_type_counts,
        "cluster_to_celltype": cluster_to_celltype,
        "n_marker_cell_types": len(markers_present),
        "n_marker_genes_used": sum(len(v) for v in markers_present.values()),
        "marker_genes_present": markers_present,
        "marker_genes_missing": markers_missing,
        "min_score": min_score,
        "min_margin": min_margin,
    }

    result = {
        "status": "success" if not warnings else "partial",
        "message": (
            "Cluster Annotation Summary:\n"
            f"Cluster key: {cluster_key}\n"
            f"Output key: {out_key}\n"
            f"Clusters annotated: {results['n_clusters']}\n"
            f"Cell types found: {', '.join(cell_type_counts.keys())}\n"
        ),
        "warnings": warnings,
        "results": results,
        "processing_state_before": {},
        "processing_state_after": {
            "shape": (int(adata.n_obs), int(adata.n_vars)),
            "has_cell_type_annotation": out_key in adata.obs.columns,
            "cell_type_columns": [
                col for col in adata.obs.columns if "cell_type" in str(col).lower()
            ],
        },
    }

    return adata, result
