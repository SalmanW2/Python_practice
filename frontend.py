from fastapi import APIRouter, Request, Form, Depends, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from database import (get_all_users, update_user_status, is_blocked, verify_admin_password, 
                      set_admin_password, get_admin_role, get_all_admins, add_new_admin, 
                      remove_admin, get_all_blocked, remove_blocked_record)
from auth import get_admin_login_url
import logging

frontend_router = APIRouter()
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
        </style>
    </head>
    <body class="bg-slate-50 text-slate-900">
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
                <a href="https://t.me/Private_Mail_Assistent_Bot" class="bg-blue-600 text-white px-8 py-4 rounded-xl shadow-xl hover:bg-blue-700 transition-all font-bold text-lg">Start on Telegram</a>
                <a href="#features" class="bg-white border border-slate-200 px-8 py-4 rounded-xl shadow-sm hover:bg-slate-50 transition-all font-bold text-lg text-slate-700">Learn More</a>
            </div>
        </main>

        <section id="features" class="py-20 bg-white border-t border-slate-200">
            <div class="max-w-7xl mx-auto px-6">
                <div class="text-center mb-16">
                    <h2 class="text-4xl font-bold text-slate-800">How It Works</h2>
                    <p class="text-slate-500 mt-4 text-lg">Your personal AI assistant working 24/7 inside Telegram.</p>
                </div>
                <div class="grid md:grid-cols-3 gap-10">
                    <div class="p-8 bg-slate-50 rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow">
                        <div class="text-4xl mb-4">📝</div>
                        <h3 class="text-xl font-bold text-slate-800 mb-3">Smart Summaries</h3>
                        <p class="text-slate-600">Stop reading long threads. Our AI extracts the core message and action items from your emails instantly.</p>
                    </div>
                    <div class="p-8 bg-slate-50 rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow">
                        <div class="text-4xl mb-4">✍️</div>
                        <h3 class="text-xl font-bold text-slate-800 mb-3">Draft Replies</h3>
                        <p class="text-slate-600">Tell the bot what you want to say in simple words, and it will generate a professional, context-aware email draft.</p>
                    </div>
                    <div class="p-8 bg-slate-50 rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow">
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
async def admin_login_page(error: str = "", msg: str = ""):
    alert_html = ""
    if error:
        alert_html = f'<div class="bg-red-100 text-red-700 p-3 rounded-lg mb-4 text-sm font-semibold">{error}</div>'
    elif msg:
        alert_html = f'<div class="bg-green-100 text-green-700 p-3 rounded-lg mb-4 text-sm font-semibold">{msg}</div>'

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
                <p class="text-slate-500 mt-2 text-sm">Secure access for authorized personnel.</p>
            </div>
            
            {alert_html}

            <div class="text-center mb-6">
                <button onclick="window.location.href='/admin/auth/google'" class="w-full flex items-center justify-center gap-3 bg-white border border-slate-300 p-3 rounded-lg hover:bg-slate-50 transition-all shadow-sm">
                    <img src="https://www.google.com/favicon.ico" class="w-5 h-5">
                    <span class="font-semibold text-slate-700">Continue with Google</span>
                </button>
            </div>

            <div class="relative flex py-4 items-center">
                <div class="flex-grow border-t border-slate-200"></div>
                <span class="flex-shrink mx-4 text-slate-400 text-sm font-semibold">OR</span>
                <div class="flex-grow border-t border-slate-200"></div>
            </div>

            <div class="text-center mb-4">
                <p class="text-xs text-slate-500 mb-3 px-2">If you have configured a password, login below:</p>
            </div>
            <form action="/admin/login_with_password" method="POST" class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1 text-left">Email Address</label>
                    <input type="email" name="email" required class="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none">
                </div>
                <div>
                    <label class="block text-sm font-medium text-slate-700 mb-1 text-left">Password</label>
                    <input type="password" name="password" required class="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none">
                </div>
                <button type="submit" class="w-full bg-slate-900 text-white p-3 rounded-lg font-bold hover:bg-slate-800 transition-all shadow-md">Login to Dashboard</button>
            </form>
        </div>
    </body>
    </html>
    """

@frontend_router.post("/admin/login_with_password")
async def login_with_password(response: Response, email: str = Form(...), password: str = Form(...)):
    """Handles manual password login for admins."""
    if verify_admin_password(email, password):
        response = RedirectResponse(url="/admin/dashboard", status_code=302)
        response.set_cookie(key="admin_session", value=email, max_age=86400)
        return response
    else:
        return RedirectResponse(url="/admin/login?error=Invalid Email or Password", status_code=302)

@frontend_router.get("/admin/auth/google")
async def admin_auth_google():
    url = get_admin_login_url()
    return RedirectResponse(url=url)

# --- 3. Main Admin Dashboard ---
@frontend_router.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    admin_email = request.cookies.get("admin_session")
    if not admin_email:
        return RedirectResponse(url="/admin/login")

    role = get_admin_role(admin_email)
    manage_admins_tab = ""
    if role == "super_admin":
        manage_admins_tab = f'<a href="#" onclick="showSection(\'manage-admins-section\', this)" class="nav-link block p-3 hover:bg-slate-800 text-slate-400 rounded-lg transition-all">Manage Admins</a>'

    # --- Generate Users HTML ---
    users = get_all_users()
    users_html = ""
    for u in users:
        is_user_blocked = is_blocked("telegram", str(u['telegram_id']))
        
        if is_user_blocked:
            status_html = '<span class="px-3 py-1 rounded-full text-xs font-bold bg-red-100 text-red-700">BLOCKED</span>'
            buttons_html = f'<button onclick="unblockUser({u["telegram_id"]})" class="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg font-bold hover:bg-gray-200 transition-all text-sm">Unblock Access</button>'
        elif u.get('is_verified'):
            status_html = '<span class="px-3 py-1 rounded-full text-xs font-bold bg-green-100 text-green-700">APPROVED</span>'
            buttons_html = f'<button onclick="openBlockModal({u["telegram_id"]})" class="bg-red-50 text-red-600 px-4 py-2 rounded-lg font-bold hover:bg-red-600 hover:text-white transition-all text-sm">Block</button>'
        else:
            status_html = '<span class="px-3 py-1 rounded-full text-xs font-bold bg-yellow-100 text-yellow-700">PENDING</span>'
            buttons_html = f'''
                <button onclick="approveUser({u['telegram_id']})" class="bg-blue-50 text-blue-600 px-4 py-2 rounded-lg font-bold hover:bg-blue-600 hover:text-white transition-all text-sm">Approve</button>
                <button onclick="openBlockModal({u['telegram_id']})" class="bg-red-50 text-red-600 px-4 py-2 rounded-lg font-bold hover:bg-red-600 hover:text-white transition-all text-sm">Block</button>
            '''

        users_html += f'''
        <tr class="user-row border-b border-slate-100 hover:bg-slate-50 transition-all">
            <td class="p-4">
                <div class="font-bold text-slate-800">{u.get('first_name', 'N/A')}</div>
                <div class="text-xs text-slate-400">ID: {u['telegram_id']} | @{u.get('username', 'none')}</div>
                <div class="text-sm text-blue-600 mt-1">{u.get('email', 'Email Not Linked')}</div>
            </td>
            <td class="p-4">{status_html}</td>
            <td class="p-4 text-sm text-slate-500">{u.get('created_at', '').split('T')[0]}</td>
            <td class="p-4 space-x-2">{buttons_html}</td>
        </tr>
        '''

    # --- Generate Blocklist HTML ---
    blocked_records = get_all_blocked()
    blocklist_html = ""
    for b in blocked_records:
        blocklist_html += f'''
        <tr class="border-b border-slate-100">
            <td class="p-4 font-semibold text-slate-800">{b['block_type'].upper()}: {b['block_value']}</td>
            <td class="p-4 text-slate-600">{b.get('reason', 'No reason provided')}</td>
            <td class="p-4"><button onclick="removeBlockRecord('{b['id']}')" class="text-blue-600 hover:underline font-semibold text-sm">Remove Block</button></td>
        </tr>
        '''
    if not blocklist_html:
        blocklist_html = '<tr><td colspan="3" class="p-4 text-slate-500">No blocked records found.</td></tr>'

    # --- Generate Admins HTML ---
    admins = get_all_admins()
    admins_html = ""
    for a in admins:
        remove_btn = f'''<button onclick="removeAdmin('{a["id"]}')" class="text-red-600 hover:underline font-semibold text-sm">Remove</button>''' if a['email'] != admin_email else '<span class="text-slate-400 text-sm">Current User</span>'
        admins_html += f'''
        <tr class="border-b border-slate-100">
            <td class="p-4 font-semibold text-slate-800">{a['email']}</td>
            <td class="p-4 text-slate-600 capitalize">{a['role'].replace('_', ' ')}</td>
            <td class="p-4">{remove_btn}</td>
        </tr>
        '''

    return f"""
    <html>
    <head>
        <title>Dashboard - Admin</title>
        {FAVICON_SVG}
        <script src="https://cdn.tailwindcss.com"></script>
        <script>
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

            function filterUsers() {{
                let input = document.getElementById('searchInput').value.toLowerCase();
                let rows = document.querySelectorAll('.user-row');
                rows.forEach(row => {{
                    let text = row.innerText.toLowerCase();
                    row.style.display = text.includes(input) ? '' : 'none';
                }});
            }}

            // --- Modal & User Actions ---
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
                if (!reason) {{ alert("Please provide a reason for blocking."); return; }}
                await fetch(`/admin/update/${{currentBlockId}}/blocked?reason=${{encodeURIComponent(reason)}}`, {{method: 'POST'}});
                location.reload();
            }}

            async function approveUser(tg_id) {{
                await fetch(`/admin/update/${{tg_id}}/approved`, {{method: 'POST'}});
                location.reload();
            }}

            async function unblockUser(tg_id) {{
                await fetch(`/admin/update/${{tg_id}}/pending`, {{method: 'POST'}});
                location.reload();
            }}

            // --- Blocklist Actions ---
            async function removeBlockRecord(recordId) {{
                if(confirm("Are you sure you want to remove this block?")) {{
                    await fetch(`/admin/remove_block/${{recordId}}`, {{method: 'POST'}});
                    location.reload();
                }}
            }}

            // --- Password Action ---
            async function savePassword(event) {{
                event.preventDefault();
                let p1 = document.getElementById('newPass').value;
                let p2 = document.getElementById('confPass').value;
                let errDiv = document.getElementById('passError');
                
                if(p1.length < 6) {{ errDiv.innerText = "Password must be at least 6 characters."; errDiv.classList.remove('hidden'); return; }}
                if(p1 !== p2) {{ errDiv.innerText = "Passwords do not match!"; errDiv.classList.remove('hidden'); return; }}
                
                errDiv.classList.add('hidden');
                let formData = new FormData();
                formData.append('password', p1);
                
                let res = await fetch('/admin/set_password', {{method: 'POST', body: formData}});
                let data = await res.json();
                if(data.status === 'ok') {{ 
                    alert("Password saved successfully!"); 
                    document.getElementById('passForm').reset(); 
                }}
            }}

            // --- Admin Management Actions ---
            async function submitNewAdmin(event) {{
                event.preventDefault();
                let email = document.getElementById('newAdminEmail').value;
                let role = document.getElementById('newAdminRole').value;
                
                let formData = new FormData();
                formData.append('email', email);
                formData.append('role', role);
                
                let res = await fetch('/admin/add_admin', {{method: 'POST', body: formData}});
                if(res.ok) location.reload();
                else alert("Error adding administrator.");
            }}

            async function removeAdmin(adminId) {{
                if(confirm("Remove this administrator?")) {{
                    await fetch(`/admin/remove_admin/${{adminId}}`, {{method: 'POST'}});
                    location.reload();
                }}
            }}
        </script>
    </head>
    <body class="bg-slate-50 min-h-screen font-sans">
        
        <div id="blockModal" class="hidden fixed inset-0 bg-slate-900 bg-opacity-50 flex items-center justify-center z-50 transition-opacity">
            <div class="bg-white p-6 rounded-2xl shadow-2xl w-full max-w-md">
                <h3 class="text-xl font-bold text-slate-800 mb-2">Block User</h3>
                <p class="text-sm text-slate-500 mb-4">Please specify the reason for blocking this user.</p>
                <input type="text" id="blockReason" placeholder="e.g., Spamming..." class="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-red-500 outline-none mb-6">
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
                    {manage_admins_tab}
                    <a href="#" onclick="showSection('set-password-section', this)" class="nav-link block p-3 hover:bg-slate-800 text-slate-400 rounded-lg transition-all">Set Password</a>
                    <div class="pt-10">
                        <a href="/admin/logout" class="block p-3 text-red-400 hover:text-red-300 hover:bg-slate-800 rounded-lg transition-all">Logout</a>
                    </div>
                </nav>
            </div>

            <div class="flex-1 p-10">
                
                <div id="users-section" class="dashboard-section">
                    <div class="flex justify-between items-center mb-10">
                        <h1 class="text-3xl font-bold text-slate-800">User Management</h1>
                        <div class="flex gap-4">
                            <input type="text" id="searchInput" onkeyup="filterUsers()" placeholder="Search Users..." class="p-3 border border-slate-300 rounded-xl w-80 shadow-sm focus:ring-2 focus:ring-blue-500 outline-none">
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
                                {users_html}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div id="blocklist-section" class="dashboard-section hidden">
                    <h1 class="text-3xl font-bold text-slate-800 mb-6">System Blocklist</h1>
                    <div class="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                        <table class="w-full text-left">
                            <thead class="bg-slate-50 border-b border-slate-200">
                                <tr>
                                    <th class="p-4 text-sm font-semibold text-slate-600">Target</th>
                                    <th class="p-4 text-sm font-semibold text-slate-600">Reason</th>
                                    <th class="p-4 text-sm font-semibold text-slate-600">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {blocklist_html}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div id="manage-admins-section" class="dashboard-section hidden">
                    <h1 class="text-3xl font-bold text-slate-800 mb-6">Manage Administrators</h1>
                    
                    <div class="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 mb-8">
                        <h2 class="text-lg font-bold text-slate-800 mb-4">Add New Admin</h2>
                        <form onsubmit="submitNewAdmin(event)" class="flex gap-4 items-end">
                            <div class="flex-1">
                                <label class="block text-sm font-medium text-slate-700 mb-1">Email Address</label>
                                <input type="email" id="newAdminEmail" required class="w-full p-3 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-blue-500">
                            </div>
                            <div class="w-64">
                                <label class="block text-sm font-medium text-slate-700 mb-1">Role</label>
                                <select id="newAdminRole" class="w-full p-3 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-blue-500 bg-white">
                                    <option value="admin">Admin</option>
                                    <option value="super_admin">Super Admin</option>
                                </select>
                            </div>
                            <button type="submit" class="bg-blue-600 text-white px-6 py-3 rounded-lg font-bold hover:bg-blue-700 h-[50px]">Add User</button>
                        </form>
                    </div>

                    <div class="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                        <table class="w-full text-left">
                            <thead class="bg-slate-50 border-b border-slate-200">
                                <tr>
                                    <th class="p-4 text-sm font-semibold text-slate-600">Email Address</th>
                                    <th class="p-4 text-sm font-semibold text-slate-600">Role</th>
                                    <th class="p-4 text-sm font-semibold text-slate-600">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {admins_html}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div id="set-password-section" class="dashboard-section hidden">
                    <h1 class="text-3xl font-bold text-slate-800 mb-6">Set Admin Password</h1>
                    <div class="bg-white p-8 rounded-2xl shadow-sm border border-slate-200 max-w-lg">
                        <p class="text-slate-500 mb-6">Create a password to login directly without using Google SSO.</p>
                        
                        <form id="passForm" onsubmit="savePassword(event)" class="space-y-4">
                            <div>
                                <label class="block text-sm font-medium text-slate-700 mb-1">New Password</label>
                                <input type="password" id="newPass" required placeholder="Minimum 6 characters" class="w-full p-3 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-blue-500">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-slate-700 mb-1">Confirm Password</label>
                                <input type="password" id="confPass" required placeholder="Retype your password" class="w-full p-3 border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-blue-500">
                                <div id="passError" class="text-red-500 text-sm mt-2 hidden font-semibold"></div>
                            </div>
                            <button type="submit" class="bg-blue-600 text-white px-6 py-3 rounded-lg font-bold hover:bg-blue-700 shadow-md">Save Password</button>
                        </form>
                    </div>
                </div>

            </div>
        </div>
    </body>
    </html>
    """

# --- 4. Success & Error Pages ---
@frontend_router.get("/callback_success", response_class=HTMLResponse)
async def success_page(msg: str, success: bool = True, is_admin_error: bool = False):
    color = "green" if success else "red"
    icon = "✅" if success else "❌"
    
    if is_admin_error:
        action_button = '<a href="/admin/login" class="bg-red-600 text-white px-8 py-3 rounded-xl font-bold shadow-lg block hover:bg-red-700 transition-colors">Retry Admin Login</a>'
        desc_text = "Please retry with an authorized administrator email address."
    else:
        action_button = '<a href="https://t.me/Private_Mail_Assistent_Bot" class="bg-blue-600 text-white px-8 py-3 rounded-xl font-bold shadow-lg block hover:bg-blue-700 transition-colors">Open Telegram</a>'
        desc_text = "You may now close this page and return to the bot."

    return f"""
    <html>
    <head>
        <title>Authentication Status</title>
        {FAVICON_SVG}
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-100 flex items-center justify-center min-h-screen font-sans">
        <div class="bg-white p-10 rounded-2xl shadow-xl text-center max-w-sm w-full border-b-8 border-{color}-500">
            <div class="text-5xl mb-6">{icon}</div>
            <h2 class="text-2xl font-bold text-slate-800 mb-2">{msg}</h2>
            <p class="text-slate-500 mb-8">{desc_text}</p>
            {action_button}
        </div>
    </body>
    </html>
    """

# --- 5. Admin API Routes ---
@frontend_router.post("/admin/update/{tg_id}/{status}")
async def change_status(tg_id: int, status: str, reason: str = ""):
    is_verified = True if status == "approved" else False
    update_user_status(tg_id, is_verified, status, reason)
    return {"status": "ok"}

@frontend_router.post("/admin/remove_block/{record_id}")
async def unblock_record(record_id: str):
    remove_blocked_record(record_id)
    return {"status": "ok"}

@frontend_router.post("/admin/set_password")
async def api_set_password(request: Request, password: str = Form(...)):
    admin_email = request.cookies.get("admin_session")
    if admin_email:
        set_admin_password(admin_email, password)
        return {"status": "ok"}
    return {"status": "error"}

@frontend_router.post("/admin/add_admin")
async def api_add_admin(request: Request, email: str = Form(...), role: str = Form(...)):
    admin_email = request.cookies.get("admin_session")
    if get_admin_role(admin_email) == "super_admin":
        add_new_admin(email, role, admin_email)
        return {"status": "ok"}
    return Response(status_code=403)

@frontend_router.post("/admin/remove_admin/{admin_id}")
async def api_remove_admin(request: Request, admin_id: str):
    admin_email = request.cookies.get("admin_session")
    if get_admin_role(admin_email) == "super_admin":
        remove_admin(admin_id)
        return {"status": "ok"}
    return Response(status_code=403)

@frontend_router.get("/admin/logout")
async def admin_logout(response: Response):
    # Logs the admin out and sends them to the login page with a success message
    response = RedirectResponse(url="/admin/login?msg=Logged out successfully")
    response.delete_cookie("admin_session")
    return response
