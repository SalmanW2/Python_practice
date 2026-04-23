from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from database import get_all_users, update_user_status, is_blocked
from auth import get_admin_login_url
import logging

frontend_router = APIRouter()

# --- 1. Public Landing Page ---
@frontend_router.get("/", response_class=HTMLResponse)
async def landing_page():
    return """
    <html>
    <head>
        <title>Smart Email Assistant</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
        <style>body { font-family: 'Inter', sans-serif; }</style>
    </head>
    <body class="bg-slate-50 text-slate-900">
        <nav class="p-6 flex justify-between items-center max-w-7xl mx-auto">
            <div class="text-2xl font-bold text-blue-600">📧 MailAgent AI</div>
            <a href="/admin/login" class="text-slate-600 hover:text-blue-600 font-semibold">Admin Login</a>
        </nav>
        <main class="flex flex-col items-center justify-center min-h-[80vh] text-center px-4">
            <h1 class="text-6xl font-extrabold tracking-tight mb-6">Apne Inbox ko <span class="text-blue-600">Agentic AI</span> se Control Karein</h1>
            <p class="text-xl text-slate-600 mb-10 max-w-2xl">
                Telegram par emails ki summaries parhein, replies draft karein, aur apna professional communication behtar banayein.
            </p>
            <div class="flex gap-4">
                <a href="https://t.me/Private_Mail_Assistent_Bot" class="bg-blue-600 text-white px-8 py-4 rounded-xl shadow-xl hover:bg-blue-700 transition-all font-bold text-lg">Start on Telegram</a>
                <a href="#features" class="bg-white border border-slate-200 px-8 py-4 rounded-xl shadow-sm hover:bg-slate-50 transition-all font-bold text-lg text-slate-700">Learn More</a>
            </div>
        </main>
    </body>
    </html>
    """

# --- 2. Admin Login Page (Hybrid Flow) ---
@frontend_router.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page():
    return """
    <html>
    <head>
        <title>Admin Login - MailAgent</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-100 flex items-center justify-center min-h-screen">
        <div class="bg-white p-10 rounded-2xl shadow-2xl w-full max-w-md">
            <div class="text-center mb-8">
                <h1 class="text-3xl font-bold text-slate-800">Admin Portal</h1>
                <p class="text-slate-500 mt-2">Apne credentials use karke login karein</p>
            </div>
            
            <button onclick="window.location.href='/admin/auth/google'" class="w-full flex items-center justify-center gap-3 bg-white border border-slate-300 p-3 rounded-lg hover:bg-slate-50 transition-all mb-6">
                <img src="https://www.google.com/favicon.ico" class="w-5 h-5">
                <span class="font-semibold text-slate-700">Continue with Google</span>
            </button>

            <div class="relative flex py-4 items-center">
                <div class="flex-grow border-t border-slate-200"></div>
                <span class="flex-shrink mx-4 text-slate-400 text-sm">OR</span>
                <div class="flex-grow border-t border-slate-200"></div>
            </div>

            <form action="/admin/dashboard" method="GET" class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Email Address</label>
                    <input type="email" name="email" required class="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none">
                </div>
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Password</label>
                    <input type="password" name="password" required class="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none">
                </div>
                <button type="submit" class="w-full bg-slate-900 text-white p-3 rounded-lg font-bold hover:bg-slate-800 transition-all">Login to Dashboard</button>
            </form>
            <p class="text-xs text-center text-slate-400 mt-6">Pehli baar login kar rahe hain? Toh Google SSO use karein.</p>
        </div>
    </body>
    </html>
    """

@frontend_router.get("/admin/auth/google")
async def admin_auth_google():
    """Button click hone par Admin ko Google par bhejta hai."""
    url = get_admin_login_url()
    return RedirectResponse(url=url)

# --- 3. Main Admin Dashboard (Secure + Live Search + Modals) ---
@frontend_router.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    # Check karein ke admin ka browser cookie mojood hai ya nahi
    admin_email = request.cookies.get("admin_session")
    if not admin_email:
        return RedirectResponse(url="/admin/login")

    users = get_all_users()
    return f"""
    <html>
    <head>
        <title>Dashboard - Admin</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script>
            // Live Search Logic
            function filterUsers() {{
                let input = document.getElementById('searchInput').value.toLowerCase();
                let rows = document.querySelectorAll('.user-row');
                rows.forEach(row => {{
                    let text = row.innerText.toLowerCase();
                    row.style.display = text.includes(input) ? '' : 'none';
                }});
            }}

            // Status Update with Block Reason Prompt
            async function updateStatus(tg_id, status) {{
                let reason = "";
                if (status === 'blocked') {{
                    reason = prompt("Block karne ki wajah (Reason) batayein:");
                    if (reason === null) return;
                }}
                await fetch(`/admin/update/${{tg_id}}/${{status}}?reason=${{encodeURIComponent(reason)}}`, {{method: 'POST'}});
                location.reload();
            }}
        </script>
    </head>
    <body class="bg-slate-50 min-h-screen">
        <div class="flex">
            <div class="w-64 bg-slate-900 text-white min-h-screen p-6 hidden lg:block">
                <div class="text-xl font-bold mb-10">Admin Control</div>
                <nav class="space-y-4">
                    <a href="#" class="block p-3 bg-blue-600 rounded-lg font-semibold">User Management</a>
                    <a href="#" class="block p-3 hover:bg-slate-800 rounded-lg text-slate-400 transition-all">Email Blacklist</a>
                    <a href="#" class="block p-3 hover:bg-slate-800 rounded-lg text-slate-400 transition-all">Role Settings</a>
                    <a href="/" class="block p-3 text-red-400 hover:text-red-300 mt-20">Logout</a>
                </nav>
            </div>

            <div class="flex-1 p-10">
                <div class="flex justify-between items-center mb-10">
                    <h1 class="text-3xl font-bold text-slate-800">User Management</h1>
                    <div class="flex gap-4">
                        <input type="text" id="searchInput" onkeyup="filterUsers()" placeholder="Search Name, ID or Email..." class="p-3 border border-slate-300 rounded-xl w-80 shadow-sm focus:ring-2 focus:ring-blue-500 outline-none">
                    </div>
                </div>

                <div class="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                    <table class="w-full text-left">
                        <thead class="bg-slate-50 border-b border-slate-200">
                            <tr>
                                <th class="p-4 text-sm font-semibold text-slate-600">Telegram User</th>
                                <th class="p-4 text-sm font-semibold text-slate-600">Status</th>
                                <th class="p-4 text-sm font-semibold text-slate-600">Registration Date</th>
                                <th class="p-4 text-sm font-semibold text-slate-600">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join([f'''
                            <tr class="user-row border-b border-slate-100 hover:bg-slate-50 transition-all">
                                <td class="p-4">
                                    <div class="font-bold text-slate-800">{u.get('first_name', 'N/A')}</div>
                                    <div class="text-xs text-slate-400">ID: {u['telegram_id']} | @{u.get('username', 'none')}</div>
                                    <div class="text-sm text-blue-600 mt-1">{u.get('email', 'Email Not Linked')}</div>
                                </td>
                                <td class="p-4">
                                    <span class="px-3 py-1 rounded-full text-xs font-bold {'bg-green-100 text-green-700' if u.get('is_verified') else 'bg-yellow-100 text-yellow-700'}">
                                        {'APPROVED' if u.get('is_verified') else 'PENDING'}
                                    </span>
                                </td>
                                <td class="p-4 text-sm text-slate-500">{u.get('created_at', '').split('T')[0]}</td>
                                <td class="p-4 space-x-2">
                                    <button onclick="updateStatus({u['telegram_id']}, 'approved')" class="bg-blue-50 text-blue-600 px-4 py-2 rounded-lg font-bold hover:bg-blue-600 hover:text-white transition-all text-sm">Approve</button>
                                    <button onclick="updateStatus({u['telegram_id']}, 'blocked')" class="bg-red-50 text-red-600 px-4 py-2 rounded-lg font-bold hover:bg-red-600 hover:text-white transition-all text-sm">Block</button>
                                </td>
                            </tr>
                            ''' for u in users])}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

# --- 4. Success Redirect Page ---
@frontend_router.get("/callback_success", response_class=HTMLResponse)
async def success_page(msg: str, success: bool = True):
    color = "green" if success else "red"
    return f"""
    <html>
    <head>
        <title>Status</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-100 flex items-center justify-center min-h-screen">
        <div class="bg-white p-10 rounded-2xl shadow-xl text-center max-w-sm w-full border-b-8 border-{color}-500">
            <div class="text-5xl mb-6">{"✅" if success else "❌"}</div>
            <h2 class="text-2xl font-bold text-slate-800 mb-2">{msg}</h2>
            <p class="text-slate-500 mb-8">Ab aap bot par wapas ja sakte hain.</p>
            <a href="https://t.me/Private_Mail_Assistent_Bot" class="bg-blue-600 text-white px-8 py-3 rounded-xl font-bold shadow-lg block">Open Telegram</a>
        </div>
    </body>
    </html>
    """

# --- 5. Admin Actions API ---
@frontend_router.post("/admin/update/{tg_id}/{status}")
async def change_status(tg_id: int, status: str, reason: str = ""):
    is_verified = True if status == "approved" else False
    # Agar status blocked hai toh is_verified ko False rakhein aur block table handle karein
    update_user_status(tg_id, is_verified, status, reason)
    return {"status": "ok"}
