# Supplier Ranking API Documentation

This document describes the endpoints available in the Supplier Ranking API, which provides access to the Q-Learning based supplier ranking system.

## Authentication

All API endpoints require authentication using a JWT token. Include the token in the Authorization header as follows:

```
Authorization: Bearer <your_jwt_token>
```

## Base URL

All API endpoints are accessible under the following base path:

```
/api/ranking/
```

## Endpoints

### 1. Submit Supplier Feedback

**Endpoint:** `POST /api/ranking/feedback/`

**Purpose:** Submit performance feedback for a supplier, which will be used to update the Q-Learning model.

**Permission:** Authenticated users

**Request Body:**

```json
{
  "supplier_id": "123",
  "product_id": "456",
  "city": "Colombo",
  "delivery_time_days": 3,
  "quality_rating": 0.8,
  "order_accuracy": 0.95,
  "issues": 0
}
```

**Required Fields:**
- `supplier_id`: ID of the supplier
- `product_id`: ID of the product
- `quality_rating`: Rating between 0 and 1

**Optional Fields:**
- `city`: City location
- `delivery_time_days`: Number of days for delivery
- `order_accuracy`: Accuracy rate between 0 and 1
- `issues`: Number of issues encountered

**Response:**

```json
{
  "message": "Feedback received and Q-table updated",
  "q_value": 0.8,
  "state": "Q3_D3_P3_S5",
  "action": "RANK_TIER_1",
  "supplier": {
    "id": "123",
    "company_name": "Test Supplier"
  },
  "product_id": "456",
  "city": "Colombo",
  "metrics": {
    "quality_score": 8.0,
    "delivery_score": 7.0,
    "price_score": 7.0,
    "service_score": 10.0,
    "overall_score": 8.0
  }
}
```

### 2. Get Ranked Suppliers

**Endpoint:** `GET /api/ranking/ranking/suppliers/`

**Purpose:** Retrieve a ranked list of suppliers for a specific product and city.

**Permission:** Authenticated users

**Query Parameters:**
- `product_id` (required): ID of the product
- `city` (optional): Filter suppliers by city

**Response:**

```json
{
  "product_id": "456",
  "city": "Colombo",
  "suppliers": [
    {
      "supplier_id": "123",
      "company_name": "Alpha Supplier",
      "score": 8.5,
      "state": "Q4_D3_P3_S5",
      "best_action": "RANK_TIER_1",
      "q_value": 0.85,
      "city": "Colombo"
    },
    {
      "supplier_id": "456",
      "company_name": "Beta Supplier",
      "score": 7.5,
      "state": "Q3_D3_P3_S5",
      "best_action": "RANK_TIER_2",
      "q_value": 0.75,
      "city": "Colombo"
    }
  ],
  "count": 2
}
```

### 3. Manual Training 

**Endpoint:** `POST /api/ranking/train/manual/`

**Purpose:** Manually trigger batch training of the Q-Learning model.

**Permission:** Admin users only

**Request Body:**

```json
{
  "iterations": 100,
  "supplier_ids": ["123", "456", "789"]
}
```

**Optional Fields:**
- `iterations`: Number of training iterations (default: 100)
- `supplier_ids`: List of specific supplier IDs to train on (default: all suppliers)

**Response:**

```json
{
  "message": "Q-table updated with historical data",
  "iterations": 100,
  "supplier_count": 3
}
```

### 4. Get Q-Values for a Supplier

**Endpoint:** `GET /api/ranking/qvalue/`

**Purpose:** Retrieve Q-values for all actions available for a specific supplier's current state.

**Permission:** Authenticated users

**Query Parameters:**
- `supplier_id` (required): ID of the supplier

**Response:**

```json
{
  "state": "Q3_D3_P3_S5",
  "supplier_id": "123",
  "company_name": "Test Supplier",
  "q_values": [
    {
      "action": "RANK_TIER_1",
      "q_value": 0.75,
      "update_count": 5
    },
    {
      "action": "EXPLORE",
      "q_value": 0.6,
      "update_count": 2
    }
  ],
  "metrics": {
    "quality_score": 8.5,
    "delivery_score": 7.0,
    "price_score": 6.5,
    "service_score": 9.0,
    "overall_score": 7.75
  }
}
```

### 5. Export Q-Table

**Endpoint:** `GET /api/ranking/qtable/`

**Purpose:** Export the entire Q-table or a filtered subset.

**Permission:** Admin users only

**Query Parameters:**
- `state` (optional): Filter by state name (partial match)
- `action` (optional): Filter by action name (partial match)
- `min_q_value` (optional): Filter by minimum Q-value
- `limit` (optional): Limit the number of results (default: 100)

**Response:**

```json
{
  "q_table_entries": [
    {
      "state": "Q4_D3_P3_S5",
      "action": "RANK_TIER_1",
      "q_value": 0.85,
      "update_count": 3
    },
    {
      "state": "Q3_D3_P3_S5",
      "action": "RANK_TIER_1",
      "q_value": 0.75,
      "update_count": 5
    },
    {
      "state": "Q3_D3_P3_S5",
      "action": "EXPLORE",
      "q_value": 0.6,
      "update_count": 2
    }
  ],
  "count": 3,
  "total_entries": 3
}
```

### 6. Update Supplier Rankings

**Endpoint:** `POST /api/ranking/rankings/update/`

**Purpose:** Explicitly calculate and store rankings for suppliers in the database. This endpoint can be used to update all supplier rankings or a specific supplier's ranking.

**Permission:** Authenticated users

**Request Body:**

```json
{
  "supplier_id": "123"  // Optional - if not provided, updates all active suppliers
}
```

**Response (For a single supplier):**

```json
{
  "message": "Ranking updated for supplier 123",
  "supplier_id": 123,
  "rank": 3,
  "tier": 2,
  "overall_score": 8.2,
  "date": "2025-05-17"
}
```

**Response (For all suppliers):**

```json
{
  "message": "Updated rankings for 15 suppliers",
  "suppliers": [
    {
      "supplier_id": 123,
      "rank": 3,
      "tier": 2,
      "overall_score": 8.2
    },
    {
      "supplier_id": 456,
      "rank": 1,
      "tier": 1,
      "overall_score": 9.5
    }
    // Additional suppliers...
  ],
  "date": "2025-05-17"
}
```

**Endpoint:** `GET /api/ranking/rankings/update/`

**Purpose:** Retrieve the most recent rankings for all suppliers or a specific supplier.

**Query Parameters:**
- `supplier_id` (optional): ID of a specific supplier to get ranking for

**Response (For a single supplier):**

```json
{
  "supplier_id": 123,
  "supplier_name": "Alpha Supplier",
  "rank": 3,
  "tier": 2,
  "overall_score": 8.2,
  "quality_score": 7.5,
  "delivery_score": 8.0,
  "price_score": 9.0,
  "service_score": 8.5,
  "date": "2025-05-17"
}
```

**Response (For all suppliers):**

```json
{
  "rankings": [
    {
      "supplier_id": 456,
      "supplier_name": "Beta Supplier",
      "rank": 1,
      "tier": 1,
      "overall_score": 9.5,
      "date": "2025-05-17"
    },
    {
      "supplier_id": 789,
      "supplier_name": "Gamma Supplier",
      "rank": 2,
      "tier": 1,
      "overall_score": 9.1,
      "date": "2025-05-17"
    }
    // Additional suppliers...
  ],
  "count": 15
}
```

## State Format

The system uses a state format of `Q{quality_level}_D{delivery_level}_P{price_level}_S{service_level}` where each level is a value between 1-5 representing the performance level in that dimension.

## Actions

The system uses the following actions:
- `RANK_TIER_1`: Rank the supplier as Tier 1 (highest)
- `RANK_TIER_2`: Rank the supplier as Tier 2
- `RANK_TIER_3`: Rank the supplier as Tier 3
- `RANK_TIER_4`: Rank the supplier as Tier 4
- `RANK_TIER_5`: Rank the supplier as Tier 5 (lowest)
- `EXPLORE`: Explore this supplier more to gather data 