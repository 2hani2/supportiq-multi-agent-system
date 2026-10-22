
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    product_name VARCHAR(150) NOT NULL,
    order_date DATE NOT NULL DEFAULT CURRENT_DATE,
    status VARCHAR(30) NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    tracking_number VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS support_tickets (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    subject VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'open',
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO customers (name, email)
VALUES
    ('Aarav Sharma', 'aarav@example.com'),
    ('Priya Nair', 'priya@example.com'),
    ('Rohan Mehta', 'rohan@example.com')
ON CONFLICT (email) DO NOTHING;

INSERT INTO orders (
    customer_id, product_name, order_date,
    status, amount, tracking_number
)
SELECT id, 'Wireless Headphones', CURRENT_DATE - 3,
       'shipped', 2499.00, 'TRK1001'
FROM customers WHERE email = 'aarav@example.com'
AND NOT EXISTS (
    SELECT 1 FROM orders WHERE tracking_number = 'TRK1001'
);

INSERT INTO orders (
    customer_id, product_name, order_date,
    status, amount, tracking_number
)
SELECT id, 'Laptop Stand', CURRENT_DATE - 7,
       'delivered', 1299.00, 'TRK1002'
FROM customers WHERE email = 'priya@example.com'
AND NOT EXISTS (
    SELECT 1 FROM orders WHERE tracking_number = 'TRK1002'
);

INSERT INTO orders (
    customer_id, product_name, order_date,
    status, amount, tracking_number
)
SELECT id, 'Mechanical Keyboard', CURRENT_DATE - 1,
       'processing', 3499.00, NULL
FROM customers WHERE email = 'rohan@example.com'
AND NOT EXISTS (
    SELECT 1 FROM orders WHERE product_name = 'Mechanical Keyboard'
      AND customer_id = (
          SELECT id FROM customers
          WHERE email = 'rohan@example.com'
      )
);

INSERT INTO support_tickets (
    customer_id, subject, description, status, priority
)
SELECT id, 'Delivery update', 'Customer wants an update on shipping.',
       'open', 'medium'
FROM customers
WHERE email = 'aarav@example.com'
AND NOT EXISTS (
    SELECT 1 FROM support_tickets
    WHERE subject = 'Delivery update'
      AND customer_id = customers.id
);
