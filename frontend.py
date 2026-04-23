from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from database import get_all_users, update_user_status, is_blocked
from auth import get_admin_login_url
import logging

frontend_router = APIRouter()

# Common Favicon (Browser Tab Logo) using an SVG Emoji
FAVICON_SVG = '<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>📧</text></svg>">'

# --- 1. Public Landing Page ---
@frontend_router.get("/", response_class=HTMLResponse)
async def landing_page():
    return f"""
    <html>
    <head>
        <title>Smart Email Assistant</title>
        {FAVICON_SVG}
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Inter', sans-serif; scroll-behavior: smooth; }}
            .watermark {{
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                font-size: 40vw;
                opacity: 0.03;
                z-index: -1;
                pointer-events: none;
            }}
        </style>
    </head>
    <body class="bg-slate-50 text-slate-900 relative">
        <div class="watermark">📧</div>
        
        <nav class="p-6 flex justify-between items-center max-w-7xl mx-auto">
            <div class="text-2xl font-bold text-blue-600 flex items-center gap-2">
                <span>📧</span> MailAgent AI
            </div>
            <a href="/admin/login" class="text-slate-600 hover:text-blue-600 font-semibold transition-colors">Admin Login</a>
        </nav>

        <main class="flex flex-col items-center justify-center min-h-[80vh] text-center px-4">
            <h1 class="text-6xl font-extrabold tracking-tight mb-6">Control Your Inbox with <span class="text-blue-600">Agentic AI</span></h1>
            <p class="text-xl text-slate-600 mb-10 max-w-2xl">
                Read email summaries, draft professional replies, and manage your communications seamlessly directly through Telegram.
            </p>
            <div class="flex gap-4">
                <a href="https://t.me/Private_Mail_Assistent_Bot" class="bg-blue-600 text-white px-8 py-4 rounded-xl shadow-xl hover:bg-blue-700 transition-all font-bold text-lg hover:-translate-y-1">Start on Telegram</a>
                <a href="#features" class="bg-white border border-slate-200 px-8 py-4 rounded-xl shadow-sm hover:bg-slate-50 transition-all font-bold text-lg text-slate-700 hover:-translate-y-1">Learn More</a>
            </div>
        </main>

        <section id="features" class="py-20 bg-white border-t border-slate-200">
            <div class="max-w-7xl mx-auto px-6">
                <div class="text-center mb-16">
                    <h2 class="text-4xl font-bold text-slate-800">How It Works</h2>
                    <p class="text-slate-500 mt-4 text-lg">Your personal AI assistant working 24/7 inside Telegram.</p>
                </div>
                <div class="grid md:grid-cols-3 gap-10">
                    <div class="p-8 bg-slate-50 rounded-2xl border border-slate-100">
                        <div class="text-4xl mb-4">📝</div>
                        <h3 class="text-xl font-bold text-slate-800 mb-3">Smart Summaries</h3>
                        <p class="text-slate-600">Stop reading long threads. Our AI extracts the core message and action items from your emails instantly.</p>
                    </div>
                    <div class="p-8 bg-slate-50 rounded-2xl border border-slate-100">
                        <div class="text-4xl mb-4">✍️</div>
                        <h3 class="text-xl font-bold text-slate-800 mb-3">Draft Replies</h3>
                        <p class="text-slate-600">Tell the bot what you want to say in simple words, and it will generate a professional, context-aware email draft.</p>
                    </div>
                    <div class="p-8 bg-slate-50 rounded-2xl border border-slate-100">
                        <div class="text-4xl mb-4">🔒</div>
                        <h3 class="text-xl font-bold text-slate-800 mb-3">Secure & Private</h3>
                        <p class="text-slate-600">Built with enterprise-grade security. We use official Google OAuth to ensure your credentials remain safe and private.</p>
                    </div>
                </div>
            </div>
        </section>
    </body>
    </html>
    """

# --- 2. Admin Login Page ---
@frontend_router.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page():
    return f"""
    <html>
    <head>
        <title>Admin Login - MailAgent</title>
        {FAVICON_SVG}
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-100 flex items-center justify-center min-h-screen font-sans">
        <div class="bg-white p-10 rounded-2xl shadow-2xl w-full max-w-md">
            <div class="text-center mb-8">
                <h1 class="text-3xl font-bold text-slate-800">Admin Portal</h1>
                <p class="text-slate-500 mt-2 text-sm">Login with your email and password.</p>
            </div>
            
            <form action="/admin/dashboard" method="GET" class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Email Address</label>
                    <input type="email" name="email" required placeholder="admin@example.com" class="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none">
                </div>
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1">Password</label>
                    <input type="password" name="password" required placeholder="••••••••" class="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none">
                </div>
                <button type="submit" class="w-full bg-slate-900 text-white p-3 rounded-lg font-bold hover:bg-slate-800 transition-all">Login to Dashboard</button>
            </form>

            <div class="relative flex py-6 items-center">
                <div class="flex-grow border-t border-slate-200"></div>
                <span class="flex-shrink mx-4 text-slate-400 text-sm font-semibold">OR</span>
                <div class="flex-grow border-t border-slate-200"></div>
            </div>

            <div class="text-center mb-4">
                <p class="text-xs text-slate-500 mb-3 px-4">If you haven't set a password yet, or forgot it, please use Google Login.</p>
                <button onclick="window.location.href='/admin/auth/google'" class="w-full flex items-center justify-center gap-3 bg-white border border-slate-300 p-3 rounded-lg hover:bg-slate-50 transition-all shadow-sm">
                    <img src="https://www.google.com/favicon.ico" class="w-5 h-5">
                    <span class="font-semibold text-slate-700">Continue with Google</span>
                </button>
            </div>
        </div>
    </body>
    </html>
    """

@frontend_router.get("/admin/auth/google")
async def admin_auth_google():
    """Redirects the Admin to the Google OAuth consent screen."""
    url = get_admin_login_url()
    return RedirectResponse(url=url)

# --- 3. Main Admin Dashboard ---
@frontend_router.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    # Security: Verify browser cookie
    admin_email = request.cookies.get("admin_session")
    if not admin_email:
        return RedirectResponse(url="/admin/login")

    users = get_all_users()
    return f"""
    <html>
    <head>
        <title>Dashboard - Admin</title>
        {FAVICON_SVG}
        <script src="https://cdn.tailwindcss.com"></script>
        <script>
            // Tab Navigation Logic
            function showSection(sectionId, element) {{
                document.querySelectorAll('.dashboard-section').forEach(el => el.classList.add('hidden'));
                document.getElementById(sectionId).classList.remove('hidden');
                
                document.querySelectorAll('.nav-link').forEach(el => {{
                    el.classList.remove('bg-blue-600', 'text-white', 'font-semibold');
                    el.classList.add('hover:bg-slate-800', 'text-slate-400');
                }});
                
                element.classList.remove('hover:bg-slate-800', 'text-slate-400');
                element.classList.add('bg-blue-600', 'text-white', 'font-semibold');
            }}

            // Live Search
            function filterUsers() {{
                let input = document.getElementById('searchInput').value.toLowerCase();
                let rows = document.querySelectorAll('.user-row');
                rows.forEach(row => {{
                    let text = row.innerText.toLowerCase();
                    row.style.display = text.includes(input) ? '' : 'none';
                }});
            }}

            // Custom Modal Logic for Blocking
            let currentBlockId = null;

            function openBlockModal(tg_id) {{
                currentBlockId = tg_id;
                document.getElementById('blockModal').classList.remove('hidden');
            }}

            function closeBlockModal() {{
                currentBlockId = null;
                document.getElementById('blockReason').value = '';
                document.getElementById('blockModal').classList.add('hidden');
            }}

            async function submitBlock() {{
                let reason = document.getElementById('blockReason').value;
                if (!reason) {{
                    alert("Please provide a reason for blocking.");
                    return;
                }}
                await fetch(`/admin/update/${{currentBlockId}}/blocked?reason=${{encodeURIComponent(reason)}}`, {{method: 'POST'}});
                location.reload();
            }}

            async function approveUser(tg_id) {{
                await fetch(`/admin/update/${{tg_id}}/approved`, {{method: 'POST'}});
                location.reload();
            }}
        </script>
    </head>
    <body class="bg-slate-50 min-h-screen font-sans">
        
        <div id="blockModal" class="hidden fixed inset-0 bg-slate-900 bg-opacity-50 flex items-center justify-center z-50 transition-opacity">
            <div class="bg-white p-6 rounded-2xl shadow-2xl w-full max-w-md">
                <h3 class="text-xl font-bold text-slate-800 mb-2">Block User</h3>
                <p class="text-sm text-slate-500 mb-4">Please specify the reason for blocking this user. This will be saved in the database.</p>
                <input type="text" id="blockReason" placeholder="e.g., Spamming, Unauthorized access..." class="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none mb-6">
                <div class="flex justify-end gap-3">
                    <button onclick="closeBlockModal()" class="px-4 py-2 rounded-lg font-semibold text-slate-600 hover:bg-slate-100">Cancel</button>
                    <button onclick="submitBlock()" class="px-4 py-2 bg-red-600 text-white rounded-lg font-semibold hover:bg-red-700 shadow-md">Confirm Block</button>
                </div>
            </div>
        </div>

        <div class="flex">
            <div class="w-64 bg-slate-900 text-white min-h-screen p-6 hidden lg:block">
                <div class="text-2xl font-bold mb-10 flex items-center gap-2"><span>📧</span> Admin Panel</div>
                <nav class="space-y-2">
                    <a href="#" onclick="showSection('users-section', this)" class="nav-link block p-3 bg-blue-600 text-white font-semibold rounded-lg transition-all">User Management</a>
                    <a href="#" onclick="showSection('blocklist-section', this)" class="nav-link block p-3 hover:bg-slate-800 text-slate-400 rounded-lg transition-all">Blocklist</a>
                    <a href="#" onclick="showSection('manage-admins-section', this)" class="nav-link block p-3 hover:bg-slate-800 text-slate-400 rounded-lg transition-all">Manage Admins</a>
                    <a href="#" onclick="showSection('set-password-section', this)" class="nav-link block p-3 hover:bg-slate-800 text-slate-400 rounded-lg transition-all">Set Password</a>
                    <div class="pt-10">
                        <a href="/" class="block p-3 text-red-400 hover:text-red-300 hover:bg-slate-800 rounded-lg transition-all">Logout</a>
                    </div>
                </nav>
            </div>

            <div class="flex-1 p-10">
                
                <div id="users-section" class="dashboard-section">
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
                                        <button onclick="approveUser({u['telegram_id']})" class="bg-blue-50 text-blue-600 px-4 py-2 rounded-lg font-bold hover:bg-blue-600 hover:text-white transition-all text-sm">Approve</button>
                                        <button onclick="openBlockModal({u['telegram_id']})" class="bg-red-50 text-red-600 px-4 py-2 rounded-lg font-bold hover:bg-red-600 hover:text-white transition-all text-sm">Block</button>
                                    </td>
                                </tr>
                                ''' for u in users])}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div id="blocklist-section" class="dashboard-section hidden">
                    <h1 class="text-3xl font-bold text-slate-800 mb-6">System Blocklist</h1>
                    <div class="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
                        <p class="text-slate-500">This section will display all blocked Telegram IDs and Emails. Data will be fetched from the 'blocked_users' table.</p>
                        </div>
                </div>

                <div id="manage-admins-section" class="dashboard-section hidden">
                    <h1 class="text-3xl font-bold text-slate-800 mb-6">Manage Administrators</h1>
                    <div class="bg-yellow-50 border border-yellow-200 text-yellow-800 p-4 rounded-lg mb-6">
                        <strong>Note:</strong> Only Super Admins can add or remove other administrators.
                    </div>
                    <div class="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
                        <p class="text-slate-500">List of current admins and form to add new admins will appear here.</p>
                    </div>
                </div>

                <div id="set-password-section" class="dashboard-section hidden">
                    <h1 class="text-3xl font-bold text-slate-800 mb-6">Set Admin Password</h1>
                    <div class="bg-white p-8 rounded-2xl shadow-sm border border-slate-200 max-w-lg">
                        <p class="text-slate-500 mb-6">Create a password to login directly without using Google SSO.</p>
                        <form class="space-y-4">
                            <div>
                                <label class="block text-sm font-medium text-slate-700 mb-1">New Password</label>
                                <input type="password" class="w-full p-3 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-blue-500">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-slate-700 mb-1">Confirm Password</label>
                                <input type="password" class="w-full p-3 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-blue-500">
                            </div>
                            <button type="button" class="bg-blue-600 text-white px-6 py-3 rounded-lg font-bold hover:bg-blue-700">Save Password</button>
                        </form>
                    </div>
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
    icon = "✅" if success else "❌"
    return f"""
    <html>
    <head>
        <title>Status Update</title>
        {FAVICON_SVG}
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-100 flex items-center justify-center min-h-screen font-sans">
        <div class="bg-white p-10 rounded-2xl shadow-xl text-center max-w-sm w-full border-b-8 border-{color}-500">
            <div class="text-5xl mb-6">{icon}</div>
            <h2 class="text-2xl font-bold text-slate-800 mb-2">{msg}</h2>
            <p class="text-slate-500 mb-8">You may now close this page and return to the bot.</p>
            <a href="https://t.me/Private_Mail_Assistent_Bot" class="bg-blue-600 text-white px-8 py-3 rounded-xl font-bold shadow-lg block hover:bg-blue-700 transition-colors">Open Telegram</a>
        </div>
    </body>
    </html>
    """

# --- 5. Admin Actions API ---
@frontend_router.post("/admin/update/{tg_id}/{status}")
async def change_status(tg_id: int, status: str, reason: str = ""):
    """Updates user verification status and handles database blocking logic."""
    is_verified = True if status == "approved" else False
    # If status is blocked, keep is_verified as False and insert into block table
    update_user_status(tg_id, is_verified, status, reason)
    return {"status": "ok"}
