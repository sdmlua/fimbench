"""
Test: publish extents to ArcGIS Online (fimbench.publish.PublishFIMExtent2ArcGISOnline).

Needs the optional .[publish] extra (arcgis).
"""

CLIENT_ID = "m4zR1DBSDiJQpxsH"

import fimbench


def test_publish_to_agol():
    gis = fimbench.PublishFIMExtent2ArcGISOnline.connect_gis_oauth(client_id=CLIENT_ID)
    publisher = fimbench.PublishFIMExtent2ArcGISOnline(
        mode_used="init",
        geojson_item_id=None,
        feature_layer_item_id="",
        feature_layer_url=None,
        feature_layer_title=None,
    )
    # Title / tags / summary / description / folder default to FIMbench values.
    # Pass your own to override any of them.
    result = publisher.upsert_geojson_feature_layer(
        gis=gis,
        geojson_path="./out/FIM_extents.geojson",
        mode="auto",
        published_item_id=None,
        # title="My Layer",
        # tags="my, tags",
        # summary="My summary",
        # description="My description",
        # folder="MyFolder",
    )
    print(f"\nSuccessfully {result.mode_used} layer!")
    print(f"Feature Layer Item ID: {result.feature_layer_item_id}")
    print(f"Feature Layer URL: {result.feature_layer_url}")


if __name__ == "__main__":
    # test_publish_to_agol()
    pass
