"""
Author: Supath Dhital
Date created: January 2026

Create or update an ArcGIS Online Hosted Feature Layer from a GeoJSON file.

Workflow:
  - NEW:   add GeoJSON item -> publish Hosted Feature Layer
  - UPDATE: overwrite existing Hosted Feature Layer (by item id)
Notes:
  - GeoJSON should be WGS84 (EPSG:4326).
  - overwrite() works for Hosted Feature Layer COLLECTION items
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time
from typing import Optional

from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection

# Default FIMbench item metadata. Used when the caller does not pass its own;
# any of these can be overridden per call (or a user can supply all of them).
DEFAULT_TITLE = "BenchFIMExtents"
DEFAULT_TAGS = (
    "FIM, Flood Mapping, Benchmark FIM, Aerial Flood Extents, Hydrology, Planet, Sentinel"
)
DEFAULT_SUMMARY = (
    "Curated benchmark Flood Inundation Maps (FIMs) from remote sensing, aerial observations, "
    "and hydrodynamic models. Organized into quality-based tiers with HWM-derived flood maps. "
    "Hosted on AWS S3 with open API access."
)
DEFAULT_DESCRIPTION = (
    "Flood Inundation Mapping Benchmark (FIMbench) Repository- This repository provides a curated collection of benchmark Flood Inundation Maps (FIMs) "
    "derived from multiple high-quality sources, including remote sensing imagery, aerial observations, and high-fidelity hydrodynamic model outputs. "
    "The complete FIM inventory is organized into four quality-based tiers, along with an additional category containing High Water Mark (HWM)-derived flood maps. "
    "All benchmark datasets are hosted in an AWS S3 bucket and can be accessed through an open API, enabling seamless integration into research pipelines, "
    "visualization tools, and operational workflows."
)
DEFAULT_FOLDER = "BenchFIMData"


@dataclass
class PublishFIMExtent2ArcGISOnline:
    mode_used: str
    geojson_item_id: Optional[str]
    feature_layer_item_id: str
    feature_layer_url: Optional[str]
    feature_layer_title: Optional[str]

    @staticmethod
    def connect_gis_oauth(
        client_id: str,
        portal_url: str = "https://www.arcgis.com",
        verify_cert: bool = True,
    ) -> GIS:
        """
        OAuth interactive login (opens browser).
        """
        gis = GIS(portal_url, client_id=client_id, verify_cert=verify_cert)
        _ = gis.users.me.username
        return gis

    @staticmethod
    def _assert_file_exists(p: Path) -> None:
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(f"GeoJSON file not found: {p}")

    @staticmethod
    def _safe_name(s: str) -> str:
        out = []
        for ch in (s or "").strip():
            if ch.isalnum():
                out.append(ch)
            elif ch in {" ", "-", "."}:
                out.append("_")
        cleaned = "".join(out).strip("_")
        return cleaned[:60] or f"service_{int(time.time())}"

    @staticmethod
    def _ensure_folder_exists(gis: GIS, folder_name: str) -> str:
        """
        Ensure folder exists in user's content. Create it if it doesn't exist.
        Returns the folder name if successful.
        """
        if not folder_name:
            return None

        user = gis.users.me

        # Check if folder already exists
        existing_folders = user.folders
        for f in existing_folders:
            if f["title"] == folder_name:
                return folder_name  # Folder exists

        # Folder doesn't exist, create it
        result = gis.content.create_folder(folder_name)
        if result is None:
            raise RuntimeError(f"Failed to create folder: {folder_name}")

        return folder_name

    def create_hosted_feature_layer_from_geojson(
        self,
        gis: GIS,
        geojson_path: str | Path,
        title: str,
        service_name: Optional[str] = None,
        tags: str = "",
        summary: str = "",
        description: str = "",
        folder: Optional[str] = None,
    ) -> PublishFIMExtent2ArcGISOnline:
        """
        Upload GeoJSON as an item, then publish it as a Hosted Feature Layer (new service).

        Parameters:
        -----------
        gis : GIS
            Authenticated GIS connection object.
        geojson_path : str | Path
            Path to the GeoJSON file to upload.
        title : str
            Title for the item and hosted feature layer.
        service_name : Optional[str]
            Name for the hosted feature service. Auto-generated if not provided.
        tags : str
            Comma-separated tags for the item.
        summary : str
            Short summary/snippet for the item (appears in search results).
        description : str
            Full description of the item.
        folder : Optional[str]
            Folder name in ArcGIS Online to store the item. Created if doesn't exist.

        Returns:
        --------
        PublishFIMExtent2ArcGISOnline
            Dataclass with published item details.
        """
        geojson_path = Path(geojson_path)
        self._assert_file_exists(geojson_path)

        # Ensure folder exists before uploading
        if folder:
            folder = self._ensure_folder_exists(gis, folder)

        # Upload item
        # Using dict instead of ItemProperties to avoid 'type' keyword errors
        # 'snippet' is the ArcGIS API field name for summary
        item_props = {
            "title": title,
            "type": "GeoJson",
            "tags": tags,
            "snippet": summary,  # Summary/snippet field in ArcGIS
            "description": description,
        }

        geojson_item = gis.content.add(
            item_properties=item_props,
            data=str(geojson_path),
            folder=folder,
        )
        if geojson_item is None:
            raise RuntimeError("Failed to upload GeoJSON item (gis.content.add returned None).")

        # Publish hosted feature layer
        if not service_name:
            service_name = f"{self._safe_name(title)}_{int(time.time())}"

        fl_item = geojson_item.publish(publish_parameters={"name": service_name})
        if fl_item is None:
            raise RuntimeError("Publish failed (publish returned None).")

        # Update the published feature layer with summary if provided
        if summary:
            fl_item.update(item_properties={"snippet": summary})

        return PublishFIMExtent2ArcGISOnline(
            mode_used="new",
            geojson_item_id=geojson_item.id,
            feature_layer_item_id=fl_item.id,
            feature_layer_url=getattr(fl_item, "url", None),
            feature_layer_title=getattr(fl_item, "title", None),
        )

    def overwrite_hosted_feature_layer(
        self,
        gis: GIS,
        published_item_id: str,
        geojson_path: str | Path,
        summary: Optional[str] = None,
    ) -> PublishFIMExtent2ArcGISOnline:
        """
        Overwrite an existing Hosted Feature Layer (keeps same item id and service url).
        published_item_id must be the *Hosted Feature Layer item id* (not the original GeoJSON item).

        Parameters:
        -----------
        gis : GIS
            Authenticated GIS connection object.
        published_item_id : str
            Item ID of the existing hosted feature layer to overwrite.
        geojson_path : str | Path
            Path to the new GeoJSON file.
        summary : Optional[str]
            Updated summary/snippet for the item. If provided, updates the item metadata.

        Returns:
        --------
        PublishFIMExtent2ArcGISOnline
            Dataclass with updated item details.
        """
        geojson_path = Path(geojson_path)
        self._assert_file_exists(geojson_path)

        fl_item = gis.content.get(published_item_id)
        if fl_item is None:
            raise RuntimeError(f"Could not find item with id: {published_item_id}")

        # Overwrite uses FeatureLayerCollection manager
        flc = FeatureLayerCollection.fromitem(fl_item)
        _ = flc.manager.overwrite(str(geojson_path))

        # Update summary if provided
        if summary:
            fl_item.update(item_properties={"snippet": summary})

        return PublishFIMExtent2ArcGISOnline(
            mode_used="update",
            geojson_item_id=None,
            feature_layer_item_id=fl_item.id,
            feature_layer_url=getattr(fl_item, "url", None),
            feature_layer_title=getattr(fl_item, "title", None),
        )

    def upsert_geojson_feature_layer(
        self,
        gis: GIS,
        geojson_path: str | Path,
        mode: str = "auto",
        published_item_id: Optional[str] = None,
        title: Optional[str] = None,
        service_name: Optional[str] = None,
        tags: Optional[str] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        folder: Optional[str] = None,
    ) -> PublishFIMExtent2ArcGISOnline:
        """
        One entry-point:
        - mode="new": create new hosted feature layer (needs title)
        - mode="update": overwrite existing (needs published_item_id)
        - mode="auto": if published_item_id is provided -> update else -> new

        Parameters:
        -----------
        gis : GIS
            Authenticated GIS connection object.
        geojson_path : str | Path
            Path to the GeoJSON file.
        mode : str
            Operation mode: "auto", "new", or "update".
        published_item_id : Optional[str]
            Item ID for update mode.
        title : Optional[str]
            Title for new items. Defaults to the FIMbench title if None.
        service_name : Optional[str]
            Service name for new items.
        tags : Optional[str]
            Comma-separated tags. Defaults to the FIMbench tags if None.
        summary : Optional[str]
            Short summary/snippet. Defaults to the FIMbench summary if None.
        description : Optional[str]
            Full description. Defaults to the FIMbench description if None.
        folder : Optional[str]
            Folder name in ArcGIS Online. Defaults to the FIMbench folder if None.

        All metadata fields default to FIMbench values; pass your own to override.

        Returns:
        --------
        PublishFIMExtent2ArcGISOnline
            Dataclass with item details (ids and url).
        """
        mode = (mode or "").strip().lower()
        if mode not in {"auto", "new", "update"}:
            raise ValueError('mode must be one of: "auto", "new", "update"')

        # Fall back to the FIMbench defaults; a user-supplied value always wins.
        title = title if title is not None else DEFAULT_TITLE
        tags = tags if tags is not None else DEFAULT_TAGS
        summary = summary if summary is not None else DEFAULT_SUMMARY
        description = description if description is not None else DEFAULT_DESCRIPTION
        folder = folder if folder is not None else DEFAULT_FOLDER

        if mode in {"update"} or (mode == "auto" and published_item_id):
            if not published_item_id:
                raise ValueError("published_item_id is required for update mode.")
            return self.overwrite_hosted_feature_layer(
                gis=gis,
                published_item_id=published_item_id,
                geojson_path=geojson_path,
                summary=summary,
            )

        if not title:
            raise ValueError("title is required to create a new hosted feature layer.")

        return self.create_hosted_feature_layer_from_geojson(
            gis=gis,
            geojson_path=geojson_path,
            title=title,
            service_name=service_name,
            tags=tags,
            summary=summary,
            description=description,
            folder=folder,
        )
