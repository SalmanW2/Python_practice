from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from database import get_all_users, update_user_status

admin_router = APIRouter()

@admin_router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard():
    users = get_all_users()
    
    # HTML with Tailwind CSS
    html_content = """
    <html>
    <head>
        <title>Smart Email Assistant - Admin</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script>
            async function updateStatus(tg_id, status) {
                await fetch(`/admin/update/${tg_id}/${status}`, {method: 'POST'});
                location.reload();
            }
        </script>
    </head>
    <body class="bg-gray-100 p-8 font-sans">
        <div class="max-w-6xl mx-auto bg-white p-6 rounded-lg shadow-lg">
            <h1 class="text-3xl font-bold text-gray-800 mb-6">User Management Panel</h1>
            <table class="w-full text-left border-collapse">
                <thead>
                    <tr class="bg-gray-800 text-white">
                        <th class="p-3">TG ID</th>
                        <th class="p-3">Name</th>
                        <th class="p-3">Email</th>
                        <th class="p-3">Status</th>
                        <th class="p-3">Actions</th>
                    </tr>
                </thead>
                <tbody>
    """
    for u in users:
        status_color = "text-yellow-600" if u['status'] == 'pending' else "text-green-600" if u['status'] == 'approved' else "text-red-600"
        html_content += f"""
                    <tr class="border-b hover:bg-gray-50">
                        <td class="p-3">{u['telegram_id']}</td>
                        <td class="p-3">{u.get('first_name', '')} <br> <span class="text-xs text-gray-500">@{u.get('username', '')}</span></td>
                        <td class="p-3">{u.get('email', 'Not Linked')}</td>
                        <td class="p-3 font-bold {status_color}">{u['status'].upper()}</td>
                        <td class="p-3">
                            <button onclick="updateStatus({u['telegram_id']}, 'approved')" class="bg-green-500 text-white px-3 py-1 rounded hover:bg-green-600 text-sm">Approve</button>
                            <button onclick="updateStatus({u['telegram_id']}, 'blocked')" class="bg-red-500 text-white px-3 py-1 rounded hover:bg-red-600 text-sm ml-2">Block</button>
                        </td>
                    </tr>
        """
    
    html_content += """
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@admin_router.post("/admin/update/{tg_id}/{status}")
async def change_status(tg_id: int, status: str):
    update_user_status(tg_id, status)
    return {"message": "Updated"}
