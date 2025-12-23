# Wi-Fi Portal Server (Flask)

This is the backend for the Public Wi-Fi Management System. It handles M-Pesa payments, session management, and Mikrotik Router authorization.

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL (or SQLite for dev)
- A Mikrotik Router (for production)

### Installation

1.  **Clone the repository** and navigate to this folder.
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Environment Variables**:
    Create a `.env` file in this directory with the following content:

    ```env
    FLASK_APP=app.py
    FLASK_ENV=development
    DATABASE_URL=sqlite:///app.db
    SECRET_KEY=your_secret_key

    # M-Pesa (Sandbox)
    MPESA_CONSUMER_KEY=your_kye
    MPESA_CONSUMER_SECRET=your_secret
    MPESA_SHORTCODE=174379
    MPESA_PASSKEY=bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919
    BASE_URL=http://your_public_ip:5000

    # Mikrotik
    MIKROTIK_HOST=192.168.88.1
    MIKROTIK_USERNAME=admin
    MIKROTIK_PASSWORD=password
    FRONTEND_URL=http://localhost:5173
    ```

4.  **Initialize Database**:

    ```bash
    flask db upgrade
    ```

5.  **Run Server**:
    ```bash
    flask run
    ```

---

## 📡 Mikrotik Router Configuration

This system uses a **Walled Garden** approach. The router allows access _only_ to the payment portal and M-Pesa usage until the user pays.

### 1. Walled Garden Setup (WinBox)

Allow access to the Server and Safaricom APIs for unauthenticated users.

1.  Go to **IP** -> **Hotspot** -> **Walled Garden**.
2.  Add Rule: **Dst. Host** = `*safaricom.co.ke` (Action: allow).
3.  Add Rule: **Dst. Address** = `YOUR_SERVER_IP` (Action: allow).
    - _Note: If testing locally, allow your laptop's IP._

### 2. Captive Portal Redirect

Redirect users to the React Client App instead of the default Mikrotik page.

1.  Go to **IP** -> **Hotspot** -> **Server Profiles**.
2.  Open your profile -> **Login** tab.
3.  Ensure **HTTP CHAP** and **HTTP PAP** are checked.
4.  **Modify `login.html`**:
    - Download `login.html` from the router's file system (Files menu).
    - Replace the content with this redirect script:

```html
<html>
  <head>
    <meta
      http-equiv="refresh"
      content="0; url=http://YOUR_SERVER_IP:5173/portal?mac=$(mac)&ip=$(ip)"
    />
  </head>
  <body>
    Redirecting to Payment Portal...
  </body>
</html>
```

### 3. Verification

- Connect a phone to the Wi-Fi.
- You should be auto-redirected to `http://YOUR_SERVER_IP:5173/portal`.
- The URL will contain the MAC address (e.g., `?mac=A1:B2:C3...`).
