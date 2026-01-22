MATCH (e:Enemy {id: $enemy_id})
UNWIND e.dropped_items AS item_id
MATCH (i:Item {id: item_id})
MERGE (e)-[:DROPS]->(i);
