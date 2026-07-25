from fastapi.testclient import TestClient


def test_create_item_and_list_it(client: TestClient) -> None:
    payload = {
        "name": "Widget A",
        "category": "Storage",
        "sku": "WIDGET-A-001",
        "quantity": 12,
        "reorder_level": 5,
        "unit_price": "19.99",
    }

    create_response = client.post("/api/v1/items", json=payload)

    assert create_response.status_code == 201
    created_item = create_response.json()
    assert created_item["id"] > 0
    assert created_item["name"] == payload["name"]
    assert created_item["category"] == payload["category"]
    assert created_item["sku"] == payload["sku"]
    assert created_item["quantity"] == payload["quantity"]
    assert created_item["reorder_level"] == payload["reorder_level"]
    assert created_item["unit_price"] == payload["unit_price"]
    assert created_item["is_active"] is True

    list_response = client.get("/api/v1/items")

    assert list_response.status_code == 200
    items = list_response.json()
    assert len(items) == 1
    assert items[0]["id"] == created_item["id"]
    assert items[0]["sku"] == payload["sku"]
