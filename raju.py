import os
import json
import requests
import re
import time
import random
from datetime import datetime
import logging

# =====================================
# 🔧 CONFIGURATION
# =====================================

BOT_TOKEN = '8344806268:AAE8rz9MTRtRB46wg3f_d5xuAEMV8M0I_4I'  # Yahan apna token daalo
ADMIN_ID = 8333354105  # Yahan apna admin ID daalo
ADMIN_IMAGE_URL = 'https://ibb.co/FbzVqjwm'

# Channels for force join
CHANNEL_1 = '@Dark_x_gokjuu'
CHANNEL_2 = '@darkkk_goku'
INSTAGRAM_URL = 'https://www.instagram.com/__dark_hackerr_?igsh=MXI1ZHA2eWN3a292dg=='

# Credit Settings
DEFAULT_CREDITS = 7  # Changed to 7 free credits
ULTIMATE_CREDITS = 999999

# API Keys
AADHAAR_API_KEY = 'paidchx'

# =====================================
# 📋 API CONFIGURATION
# =====================================

API_CONFIG = {
    'phone': {
        'url': 'https://numapi.anshapi.workers.dev/?num={query}',
        'name': '📱 Number Info',
        'pattern': r'^[6-9]\d{9}$',
        'credits': 1,
        'example': '9876543210'
    },
    'upi': {
        'url': 'https://fampay-info.vercel.app/upi?vpa={query}',
        'name': '💳 UPI Lookup',
        'pattern': r'^[a-zA-Z0-9.\-_]+@[a-zA-Z]+$',
        'credits': 1,
        'example': 'user@paytm'
    },
    'aadhaar': {
        'url': f'https://rajan-aadhar-tofamily.vercel.app/fetch?key=RAJAN&aadhaar={{query}}&key={AADHAAR_API_KEY}',
        'name': '🆔 Aadhaar To Family  Lookup',
        'pattern': r'^\d{12}$',
        'credits': 1,
        'example': '123456789012'
    },
    'vehicle': {
        'url': 'https://ishanxstudio.space/rc?query={query}',
        'name': '🚗 Vehicle Lookup',
        'pattern': r'^[A-Z]{2}\d{1,2}[A-Z]{1,2}\d{1,4}$',
        'credits': 2,
        'example': 'WB90H3446'
    },
    'ifsc': {
        'url': 'https://ifsc.razorpay.com/{query}',
        'name': '🏦 IFSC Lookup',
        'pattern': r'^[A-Z]{4}0[A-Z0-9]{6}$',
        'credits': 1,
        'example': 'SBIN0000001'
    },
    'ip': {
        'url': 'https://ip-info.bjcoderx.workers.dev/?ip={query}',
        'name': '🌐 IP Lookup',
        'pattern': r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',
        'credits': 1,
        'example': '8.8.8.8'
    },
    'pincode': {
        'url': 'https://api.postalpincode.in/pincode/{query}',
        'name': '📮 Pincode Lookup',
        'pattern': r'^\d{6}$',
        'credits': 1,
        'example': '110001'
    }
}

# =====================================
# 🗄️ SIMPLE FILE-BASED STORAGE
# =====================================

class SimpleStorage:
    def __init__(self):
        self.data_file = 'bot_data.json'
        self.load_data()

    def load_data(self):
        try:
            with open(self.data_file, 'r') as f:
                self.data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.data = {
                'users': {},
                'search_history': [],
                'protected_numbers': [],
                'conversations': {},
                'banned_users': [],
                'joined_users': []  # Track users who joined channels
            }
            self.save_data()

    def save_data(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2)

    def ensure_user(self, user_id, username, first_name, last_name=''):
        user_key = str(user_id)
        if user_key not in self.data['users']:
            self.data['users'][user_key] = {
                'user_id': user_id,
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'credits': DEFAULT_CREDITS,  # 7 free credits
                'total_searches': 0,
                'is_banned': False,
                'ban_reason': '',
                'banned_by': None,
                'ban_date': None,
                'joined_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'last_active': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'has_joined_channels': False  # Track channel join status
            }
        else:
            self.data['users'][user_key]['last_active'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.data['users'][user_key]['username'] = username
            self.data['users'][user_key]['first_name'] = first_name
            self.data['users'][user_key]['last_name'] = last_name

        self.save_data()

    def get_user(self, user_id):
        return self.data['users'].get(str(user_id))

    def get_credits(self, user_id):
        user = self.get_user(user_id)
        return user['credits'] if user else 0

    def add_credits(self, user_id, amount):
        user = self.get_user(user_id)
        if user:
            user['credits'] += amount
            self.save_data()
            return True
        return False

    def deduct_credits(self, user_id, amount):
        user = self.get_user(user_id)
        if user and user['credits'] >= amount:
            user['credits'] -= amount
            self.save_data()
            return True
        return False

    def set_credits(self, user_id, amount):
        user = self.get_user(user_id)
        if user:
            user['credits'] = amount
            self.save_data()
            return True
        return False

    def is_banned(self, user_id):
        user = self.get_user(user_id)
        return user and user.get('is_banned', False)

    def ban_user(self, user_id, admin_id, reason='No reason provided'):
        user = self.get_user(user_id)
        if user:
            user['is_banned'] = True
            user['ban_reason'] = reason
            user['banned_by'] = admin_id
            user['ban_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.save_data()
            return True
        return False

    def unban_user(self, user_id):
        user = self.get_user(user_id)
        if user:
            user['is_banned'] = False
            user['ban_reason'] = ''
            user['banned_by'] = None
            user['ban_date'] = None
            self.save_data()
            return True
        return False

    def get_banned_users(self):
        return [user for user in self.data['users'].values() if user.get('is_banned')]

    def is_number_protected(self, phone_number):
        return any(pn['phone_number'] == phone_number for pn in self.data['protected_numbers'])

    def protect_number(self, phone_number, admin_id, reason='Admin protection'):
        if not self.is_number_protected(phone_number):
            self.data['protected_numbers'].append({
                'phone_number': phone_number,
                'protected_by': admin_id,
                'reason': reason,
                'protected_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            self.save_data()
            return True
        return False

    def get_protected_numbers(self):
        return self.data['protected_numbers']

    def add_search_history(self, user_id, username, first_name, service_type, query):
        self.data['search_history'].append({
            'user_id': user_id,
            'username': username,
            'first_name': first_name,
            'service_type': service_type,
            'query_text': query,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

        user = self.get_user(user_id)
        if user:
            user['total_searches'] = user.get('total_searches', 0) + 1

        self.save_data()

    def get_search_stats(self):
        stats = {}
        for search in self.data['search_history']:
            service_type = search['service_type']
            stats[service_type] = stats.get(service_type, 0) + 1
        return [{'service_type': k, 'count': v} for k, v in stats.items()]

    def get_total_users(self):
        return len(self.data['users'])

    def get_banned_users_count(self):
        return len(self.get_banned_users())

    def get_total_searches(self):
        return len(self.data['search_history'])

    def get_all_users(self):
        users = list(self.data['users'].values())
        users.sort(key=lambda x: x.get('joined_date', ''), reverse=True)
        return users[:100]

    def set_pending(self, chat_id, action, extra=None):
        self.data['conversations'][str(chat_id)] = {
            'pending_action': action,
            'extra_data': extra,
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.save_data()

    def get_pending(self, chat_id):
        return self.data['conversations'].get(str(chat_id))

    def clear_pending(self, chat_id):
        if str(chat_id) in self.data['conversations']:
            del self.data['conversations'][str(chat_id)]
            self.save_data()
            return True
        return False

    def mark_joined_channels(self, user_id):
        """Mark user as having joined channels"""
        user = self.get_user(user_id)
        if user:
            user['has_joined_channels'] = True
            self.save_data()
            return True
        return False

    def has_joined_channels(self, user_id):
        """Check if user has joined channels"""
        user = self.get_user(user_id)
        return user and user.get('has_joined_channels', False)

# =====================================
# 🤖 TELEGRAM BOT CLASS
# =====================================

class TelegramBot:
    def __init__(self):
        self.token = BOT_TOKEN
        self.admin_id = ADMIN_ID
        self.db = SimpleStorage()
        self.api_config = API_CONFIG
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.last_update_id = 0

        # Channel configuration
        self.channel_1 = CHANNEL_1
        self.channel_2 = CHANNEL_2
        self.instagram_url = INSTAGRAM_URL

    def normalize_phone_number(self, phone):
        cleaned = re.sub(r'[\s+\-]', '', phone)

        if cleaned.startswith('9191') and len(cleaned) == 13:
            cleaned = cleaned[2:]
        elif cleaned.startswith('91') and len(cleaned) == 12:
            cleaned = cleaned[2:]
        elif cleaned.startswith('+91') and len(cleaned) == 13:
            cleaned = cleaned[3:]

        if len(cleaned) == 10 and cleaned.isdigit():
            return cleaned
        return None

    def get_joining_info(self, user_id):
        user = self.db.get_user(user_id)
        if not user or 'joined_date' not in user:
            return None

        joining_time = datetime.strptime(user['joined_date'], '%Y-%m-%d %H:%M:%S')
        current_time = datetime.now()

        diff_seconds = int((current_time - joining_time).total_seconds())

        days = diff_seconds // (60 * 60 * 24)
        hours = (diff_seconds % (60 * 60 * 24)) // (60 * 60)
        minutes = (diff_seconds % (60 * 60)) // 60
        seconds = diff_seconds % 60

        joining_day = joining_time.strftime('%A')
        joining_date = joining_time.strftime('%d %B %Y')
        joining_time_str = joining_time.strftime('%H:%M:%S')

        current_day = current_time.strftime('%A')
        current_date = current_time.strftime('%d %B %Y')
        current_time_str = current_time.strftime('%H:%M:%S')

        return {
            'joining_day': joining_day,
            'joining_date': joining_date,
            'joining_time': joining_time_str,
            'days_ago': days,
            'hours_ago': hours,
            'minutes_ago': minutes,
            'seconds_ago': seconds,
            'current_day': current_day,
            'current_date': current_date,
            'current_time': current_time_str,
            'total_seconds': diff_seconds
        }

    def api_call(self, method, params=None):
        url = f"{self.base_url}/{method}"
        try:
            if params:
                response = requests.post(url, data=params, timeout=30)
            else:
                response = requests.post(url, timeout=30)
            return response.json()
        except Exception as e:
            logging.error(f"API call failed: {e}")
            return None

    def send_message(self, chat_id, text, keyboard=None, parse_mode='Markdown'):
        params = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        if keyboard:
            params['reply_markup'] = json.dumps(keyboard)
        return self.api_call('sendMessage', params)

    def send_photo(self, chat_id, photo, caption='', keyboard=None):
        params = {
            'chat_id': chat_id,
            'photo': photo,
            'caption': caption,
            'parse_mode': 'Markdown'
        }
        if keyboard:
            params['reply_markup'] = json.dumps(keyboard)
        return self.api_call('sendPhoto', params)

    def edit_message_text(self, chat_id, message_id, text, keyboard=None):
        params = {
            'chat_id': chat_id,
            'message_id': message_id,
            'text': text,
            'parse_mode': 'Markdown'
        }
        if keyboard:
            params['reply_markup'] = json.dumps(keyboard)
        return self.api_call('editMessageText', params)

    def get_user_photos(self, user_id):
        return self.api_call('getUserProfilePhotos', {'user_id': user_id, 'limit': 1})

    def main_keyboard(self):
        return {
            'keyboard': [
                [{'text': '📱 Number Info'}, {'text': '💳 UPI Lookup'}],
                [{'text': '🆔 Aadhaar To Family'}, {'text': '🚗 Vehicle'}],
                [{'text': '📮 Pincode'}, {'text': '🏦 IFSC'}],
                [{'text': '🌐 IP Lookup'}, {'text': '💎 My Credits'}],
                [{'text': '🛒 Buy Credits'}, {'text': 'ℹ️ Help'}, {'text': '📊 My Status'}]
            ],
            'resize_keyboard': True
        }

    def admin_keyboard(self):
        return {
            'keyboard': [
                [{'text': '📊 User Statistics'}, {'text': '👥 All Users'}],
                [{'text': '➕ Add Credits'}, {'text': '➖ Remove Credits'}],
                [{'text': '⚡ Ultimate Credits'}, {'text': '📈 Search Stats'}],
                [{'text': '🔨 Ban User'}, {'text': '🔓 Unban User'}],
                [{'text': '🛡️ Protect Number'}, {'text': '🛡️ Protected Numbers'}],
                [{'text': '🚫 Banned Users'}, {'text': '🏠 Main Menu'}]
            ],
            'resize_keyboard': True
        }

    def cancel_keyboard(self):
        return {'keyboard': [[{'text': '❌ Cancel'}]], 'resize_keyboard': True}

    def force_join_keyboard(self):
        """Keyboard for force join with channels and check button"""
        return {
            'inline_keyboard': [
                [{'text': '📢 Channel 1', 'url': f'https://t.me/{self.channel_1[1:]}'}],
                [{'text': '📢 Channel 2', 'url': f'https://t.me/{self.channel_2[1:]}'}],
                [{'text': '📷 Instagram', 'url': self.instagram_url}],
                [{'text': '✅ Check I Have Joined', 'callback_data': 'check_joined'}]
            ]
        }

    def send_typing_action(self, chat_id):
        """Send typing action"""
        self.api_call('sendChatAction', {'chat_id': chat_id, 'action': 'typing'})

    def send_upload_photo_action(self, chat_id):
        """Send upload photo action"""
        self.api_call('sendChatAction', {'chat_id': chat_id, 'action': 'upload_photo'})

    def get_updates(self):
        """Get new messages using polling"""
        params = {'offset': self.last_update_id + 1, 'timeout': 30}
        response = self.api_call('getUpdates', params)

        if response and 'result' in response:
            for update in response['result']:
                self.last_update_id = update['update_id']

                # Handle callback queries
                if 'callback_query' in update:
                    self.handle_callback(update['callback_query'])
                    continue

                # Handle regular messages
                if 'message' in update:
                    self.handle_update(update)

    def handle_callback(self, callback_query):
        """Handle callback queries"""
        data = callback_query['data']
        user_id = callback_query['from']['id']
        chat_id = callback_query['message']['chat']['id']
        message_id = callback_query['message']['message_id']

        if data == 'check_joined':
            # Check if user has joined channels (in real implementation, you'd check via Telegram API)
            # For now, we'll just mark them as joined
            self.db.mark_joined_channels(user_id)

            # Answer the callback query
            self.api_call('answerCallbackQuery', {
                'callback_query_id': callback_query['id'],
                'text': '✅ Thanks for joining! Welcome to ALL OSINT BY GOKU!',
                'show_alert': True
            })

            # Send typing action for better UX
            self.send_typing_action(chat_id)
            time.sleep(1)

            # Send new welcome message with main keyboard
            welcome_msg = self.get_welcome_message(user_id, callback_query['from']['first_name'])
            self.send_message(chat_id, welcome_msg, self.main_keyboard())

            # Delete the original force join message
            self.api_call('deleteMessage', {
                'chat_id': chat_id,
                'message_id': message_id
            })

    def handle_update(self, update):
        """Handle a single update"""
        if 'message' not in update:
            return

        msg = update['message']
        chat_id = msg['chat']['id']
        user_id = msg['from']['id']
        username = msg['from'].get('username', f'user_{user_id}')
        first_name = msg['from'].get('first_name', 'User')
        last_name = msg['from'].get('last_name', '')
        text = msg.get('text', '').strip()

        self.db.ensure_user(user_id, username, first_name, last_name)

        if self.db.is_banned(user_id) and user_id != self.admin_id:
            user = self.db.get_user(user_id)
            reason = user.get('ban_reason', 'No reason') if user else 'No reason'
            self.send_message(chat_id, f"🚫 *You are banned*\n\n*Reason:* {reason}")
            return

        # Check if user needs to join channels first
        if not self.db.has_joined_channels(user_id) and text != '/start':
            self.show_force_join(chat_id, user_id, first_name)
            return

        pending = self.db.get_pending(chat_id)
        if pending and pending['pending_action']:
            self.handle_pending(chat_id, user_id, username, first_name, text, pending)
            return

        self.handle_message(chat_id, user_id, username, first_name, text)

    def show_force_join(self, chat_id, user_id, first_name):
        """Show force join message"""
        msg = f"👋 *Welcome {first_name}!*\n\n"
        msg += "🔰 *ALL OSINT BY GOKU* 🔰\n\n"
        msg += "📋 *To use this bot, you must:*\n"
        msg += "1. Join our channels below\n"
        msg += "2. Follow our Instagram\n"
        msg += "3. Click 'Check I Have Joined'\n\n"
        msg += "🎁 *You'll get 7 FREE credits after joining!*\n\n"
        msg += "🔰 *Developer:* @gokuuuu_1\n"
        msg += "⚡ *Powered By:* @Dark_x_gokjuu"

        self.send_message(chat_id, msg, self.force_join_keyboard())

    def get_welcome_message(self, user_id, first_name):
        """Get welcome message after joining channels"""
        user = self.db.get_user(user_id)
        credits = user['credits'] if user else DEFAULT_CREDITS

        msg = "🎉 *WELCOME TO ALL OSINT BY GOKU!* 🎉\n\n"
        msg += f"👋 *Hey {first_name}!* 🌟\n\n"
        msg += "╔══════════════════════════╗\n"
        msg += "🌟 *ALL OSINT BY GOKU SYSTEM* 🌟\n"
        msg += "╚══════════════════════════╝\n\n"
        msg += "🚀 *Your Ultimate Information Hub!*\n"
        msg += "• Phone Lookups 📱\n• UPI Verification 💳\n• Aadhaar Details 🆔\n• Vehicle Info 🚗\n• And much more! ⚡\n\n"
        msg += f"💎 *FREE Credits:* {credits}\n"
        msg += "🔰 *Developer:* @gokuuuu_1\n"
        msg += "⚡ *Powered By:* @Dark_x_gokjuu\n\n"
        msg += "👇 *Tap any button below to get started!*"

        return msg

    def handle_message(self, chat_id, user_id, username, first_name, text):
        lower_text = text.lower()

        if lower_text in ['/start', 'start', '🏠 main menu']:
            if not self.db.has_joined_channels(user_id):
                self.show_force_join(chat_id, user_id, first_name)
            else:
                self.cmd_start(chat_id, user_id, first_name)
            return

        if (lower_text in ['/admin', '👑 admin panel']) and user_id == self.admin_id:
            self.send_message(chat_id, "👑 *Admin Panel*\n\nWelcome to control center!", self.admin_keyboard())
            return

        if user_id == self.admin_id:
            admin_commands = {
                '📊 user statistics': self.admin_stats,
                '👥 all users': self.admin_users,
                '➕ add credits': lambda: self.start_pending(chat_id, 'add_credits_user', "➕ *Add Credits*\n\nSend user ID:"),
                '➖ remove credits': lambda: self.start_pending(chat_id, 'remove_credits_user', "➖ *Remove Credits*\n\nSend user ID:"),
                '⚡ ultimate credits': lambda: self.start_pending(chat_id, 'ultimate_credits', "⚡ *Ultimate Credits*\n\nSend user ID:"),
                '📈 search stats': self.admin_search_stats,
                '🔨 ban user': lambda: self.start_pending(chat_id, 'ban_user_id', "🔨 *Ban User*\n\nSend user ID:"),
                '🔓 unban user': lambda: self.start_pending(chat_id, 'unban_user', "🔓 *Unban User*\n\nSend user ID:"),
                '🛡️ protect number': lambda: self.start_pending(chat_id, 'protect_number_phone', "🛡️ *Protect Number*\n\nSend phone number:"),
                '🛡️ protected numbers': self.admin_protected_list,
                '🚫 banned users': self.admin_banned_list
            }

            if lower_text in admin_commands:
                admin_commands[lower_text]()
                return

        # User commands
        user_commands = {
            '💎 my credits': lambda: self.cmd_credits(chat_id, user_id, first_name),
            '📊 my status': lambda: self.cmd_status(chat_id, user_id),
            'ℹ️ help': lambda: self.cmd_help(chat_id),
            '/help': lambda: self.cmd_help(chat_id),  # Added /help command
            '🛒 buy credits': lambda: self.cmd_buy_credits(chat_id, user_id)
        }

        if lower_text in user_commands:
            user_commands[lower_text]()
            return

        # Lookup commands
        lookups = {
            '📱 number info': 'phone',
            '💳 upi lookup': 'upi',
            '🆔 aadhaar to family': 'aadhaar',
            '🚗 vehicle': 'vehicle',
            '📮 pincode': 'pincode',
            '🏦 ifsc': 'ifsc',
            '🌐 ip lookup': 'ip'
        }

        if lower_text in lookups:
            lookup_type = lookups[lower_text]
            cfg = self.api_config[lookup_type]
            self.send_message(
                chat_id,
                f"📘 *{cfg['name']}*\n\nSend {lookup_type} to lookup.\n\n*Example:* `{cfg['example']}`",
                self.main_keyboard()
            )
            return

        # Phone number normalization check
        normalized_phone = self.normalize_phone_number(text)
        if normalized_phone:
            self.process_lookup(chat_id, user_id, username, first_name, normalized_phone, 'phone')
            return

        # Other API lookups
        for api_type, cfg in self.api_config.items():
            if re.match(cfg['pattern'], text):
                self.process_lookup(chat_id, user_id, username, first_name, text, api_type)
                return

        self.send_message(chat_id, "🤔 I didn't understand that. Use buttons or /help", self.main_keyboard())

    def start_pending(self, chat_id, action, message):
        self.db.set_pending(chat_id, action)
        self.send_message(chat_id, message, self.cancel_keyboard())

    def cmd_start(self, chat_id, user_id, first_name):
        user = self.db.get_user(user_id)
        credits = user['credits'] if user else DEFAULT_CREDITS

        # Send typing action for better UX
        self.send_typing_action(chat_id)
        time.sleep(0.5)

        photos = self.get_user_photos(user_id)
        photo_id = None
        if photos and 'result' in photos and photos['result']['photos']:
            photo_id = photos['result']['photos'][0][0]['file_id']

        msg = self.get_welcome_message(user_id, first_name)

        if photo_id:
            self.send_photo(chat_id, photo_id, msg, self.main_keyboard())
        else:
            self.send_photo(chat_id, ADMIN_IMAGE_URL, msg, self.main_keyboard())

    def cmd_credits(self, chat_id, user_id, first_name):
        credits = self.db.get_credits(user_id)
        msg = f"💎 *{first_name}'s Credits*\n\n"
        msg += f"You have *{credits} credits*\n\n"
        msg += "Each lookup costs 1 credit.\nContact @CyberHacked0 for more!\n\n"
        msg += "🔰 *Developer:* @gokuuuu_1\n"
        msg += "⚡ *Powered By:* @Dark_x_gokjuu"
        self.send_message(chat_id, msg, self.main_keyboard())

    def cmd_buy_credits(self, chat_id, user_id):
        msg = "🛒 *BUY CREDITS - PREMIUM PLANS* 🛒\n\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "💰 *BASIC PLAN* - ₹150\n"
        msg += "   ↳ 50 Credits\n"
        msg += "   ↳ Perfect for beginners\n"
        msg += "   ↳ 50 searches\n\n"

        msg += "💰 *PRO PLAN* - ₹450\n"
        msg += "   ↳ 150 Credits\n"
        msg += "   ↳ Best value for money\n"
        msg += "   ↳ 150 searches\n\n"

        msg += "💰 *PREMIUM PLAN* - ₹920\n"
        msg += "   ↳ 350 Credits\n"
        msg += "   ↳ Heavy user package\n"
        msg += "   ↳ 350 searches\n\n"

        msg += "💰 *ULTIMATE PLAN* - ₹1900\n"
        msg += "   ↳ 800 Credits\n"
        msg += "   ↳ Power user special\n"
        msg += "   ↳ 800 searches\n\n"

        msg += "💰 *MEGA PLAN* - ₹3400\n"
        msg += "   ↳ 1500 Credits\n"
        msg += "   ↳ Maximum savings\n"
        msg += "   ↳ 1500 searches\n\n"

        msg += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "📞 *HOW TO ORDER:*\n"
        msg += f"1. DM @gokuuuu_1\n"
        msg += f"2. Send your User ID: `{user_id}`\n"
        msg += "3. Choose your plan\n"
        msg += "4. Make payment\n"
        msg += "5. Credits added instantly! ✅\n\n"

        msg += "💡 *Note:* All payments are non-refundable\n\n"
        msg += "🔰 *Developer:* @gokuuuu_1\n"
        msg += "⚡ *Powered By:* DarkGoku"

        self.send_message(chat_id, msg, self.main_keyboard())

    def cmd_status(self, chat_id, user_id):
        user = self.db.get_user(user_id)
        if not user:
            return

        joining_info = self.get_joining_info(user_id)

        if joining_info:
            msg = "🟢 **ACTIVE STATUS** 🟢\n\n"
            msg += f"📅 **Join Date:** {joining_info['joining_day']}, {joining_info['joining_date']}\n"
            msg += f"⏰ **Join Time:** {joining_info['joining_time']}\n"
            msg += f"🕒 **Duration:** {joining_info['days_ago']} days, {joining_info['hours_ago']} hours, {joining_info['minutes_ago']} minutes\n\n"
            msg += f"🕐 **Current Time:** {joining_info['current_day']}, {joining_info['current_date']}\n"
            msg += f"⏱️ **Live Time:** {joining_info['current_time']}\n\n"
            msg += f"👤 **Name:** {user['first_name']}\n"
            msg += f"🔢 **User ID:** `{user['user_id']}`\n"
            msg += f"💎 **Credits:** {user['credits']}\n"
            msg += f"🔍 **Searches:** {user['total_searches']}\n\n"
            msg += "🔰 *Developer:* @gokuuuu_1\n"
            msg += "⚡ *Powered By:* DarkGoku"
        else:
            msg = "📊 *Your Status*\n\n"
            msg += f"👤 *Name:* {user['first_name']}\n"
            msg += f"🔢 *User ID:* `{user['user_id']}`\n"
            msg += f"💎 *Credits:* {user['credits']}\n"
            msg += f"🔍 *Searches:* {user['total_searches']}\n"
            msg += f"📅 *Joined:* {user['joined_date']}\n"
            msg += f"⏰ *Active:* {user['last_active']}\n\n"
            msg += "🔰 *Developer:* @gokuuuu_1\n"
            msg += "⚡ *Powered By:* @Dark_x_gokjuu"

        self.send_message(chat_id, msg, self.main_keyboard())

    def cmd_help(self, chat_id):
        msg = "ℹ️ *Help & Information*\n\n"
        msg += "*Available Lookups:*\n"
        msg += "📱 Phone Number\n💳 UPI ID\n🆔 Aadhaar\n🚗 Vehicle\n📮 Pincode\n🏦 IFSC\n🌐 IP Address\n\n"
        msg += "*How to use:*\n"
        msg += "1️⃣ Click lookup button\n2️⃣ Send info\n3️⃣ Get results!\n\n"
        msg += f"💎 Each search = 1 credit\n🎁 New users get {DEFAULT_CREDITS} free credits\n\n"
        msg += "*Need Help? Contact:* @gokuuuu_1\n\n"
        msg += "🔰 *Developer:* @gokuuuu_1\n"
        msg += "⚡ *Powered By:* @Dark_x_gokjuu"

        self.send_message(chat_id, msg, self.main_keyboard())

    def admin_users(self, chat_id):
        users = self.db.get_all_users()

        if not users:
            self.send_message(chat_id, "❌ No users found!", self.admin_keyboard())
            return

        msg = "👥 *All Users* (Last 100)\n\n"
        msg += "```\n"
        msg += f"{'Username':<15} | {'Chat ID':<10} | {'Credit':<6} | Ban | Joining Date\n"
        msg += "-----------------|-----------|--------|-----|-------------------\n"

        for user in users:
            username = user['username'] or user['first_name']
            username = (username[:12] + '..') if len(username) > 12 else username.ljust(12)
            user_id_str = str(user['user_id'])
            credits = str(user['credits'])
            ban_status = "🔴" if user['is_banned'] else "🟢"

            joining_date = user['joined_date']
            if isinstance(joining_date, str):
                joining_date = datetime.strptime(joining_date, '%Y-%m-%d %H:%M:%S')
            joining_str = joining_date.strftime('%d %b %H:%M')

            msg += f"{username:<15} | {user_id_str:<10} | {credits:<6} | {ban_status:<3} | {joining_str}\n"

        msg += "```\n\n"
        msg += "🔰 *Developer:* @gokuuuu_1\n"
        msg += "⚡ *Powered By:* DarkGoku"

        self.send_message(chat_id, msg, self.admin_keyboard())

    def process_lookup(self, chat_id, user_id, username, first_name, query, api_type):
        cfg = self.api_config[api_type]
        credits = self.db.get_credits(user_id)

        if credits < cfg['credits']:
            self.send_message(
                chat_id,
                f"❌ *Insufficient Credits Buy @CyberHacked0*\n\nNeed {cfg['credits']} credit(s).\nYour balance: {credits}",
                self.main_keyboard()
            )
            return

        if api_type == 'phone' and self.db.is_number_protected(query):
            self.send_message(chat_id, "🛡️ *Protected Number*\n\nThis number is protected.", self.main_keyboard())
            return

        if not self.db.deduct_credits(user_id, cfg['credits']):
            self.send_message(chat_id, "❌ Failed to deduct credits.", self.main_keyboard())
            return

        # Show searching animation
        search_animations = [
            "🔍 Scanning databases...",
            "🔄 Connecting to servers...",
            "📡 Fetching information...",
            "⚡ Processing data...",
            "🎯 Finalizing results..."
        ]

        processing_msg = f"🎬 *{cfg['name']} Search Started!*\n\n"
        processing_msg += f"*Query:* `{query}`\n\n"

        # Send initial processing message
        sent_msg = self.send_message(chat_id, processing_msg + " ⏳ " + random.choice(search_animations), self.main_keyboard())

        if not sent_msg or 'result' not in sent_msg or 'message_id' not in sent_msg['result']:
            self.db.add_credits(user_id, cfg['credits'])
            self.send_message(chat_id, "❌ Error sending message. Please try again.", self.main_keyboard())
            return

        msg_id = sent_msg['result']['message_id']

        # Update with animation
        for i, animation in enumerate(search_animations):
            time.sleep(1)  # Simulate processing time
            progress = "🟩" * (i + 1) + "⬜" * (len(search_animations) - i - 1)
            self.edit_message_text(
                chat_id,
                msg_id,
                processing_msg + f"{progress}\n⏳ {animation}",
                self.main_keyboard()
            )

        # Make API call
        url = cfg['url'].format(query=query)
        response = self.make_api_call(url)

        if response is None:
            self.db.add_credits(user_id, cfg['credits'])
            self.edit_message_text(
                chat_id,
                msg_id,
                f"❌ *API Error*\n\nUnable to fetch {api_type} details for: `{query}`\n\nPlease try again later or contact support.",
                self.main_keyboard()
            )
            return

        # Process and format response
        formatted_response = self.format_api_response(response, api_type, query)

        # Prepare final result
        remaining_credits = self.db.get_credits(user_id)
        result_msg = f"✅ *{cfg['name']} Result*\n\n"
        result_msg += f"*Query:* `{query}`\n\n"
        result_msg += formatted_response + "\n\n"
        result_msg += f"💎 *Remaining Credits:* {remaining_credits}\n\n"
        result_msg += "🔰 *Developer:* @gokuuuu_1\n"
        result_msg += "⚡ *Powered By:* @Dark_x_gokjuu"

        # Update message with results
        edit_result = self.edit_message_text(chat_id, msg_id, result_msg, self.main_keyboard())

        # If editing fails, send new message
        if not edit_result or not edit_result.get('ok'):
            self.send_message(chat_id, result_msg, self.main_keyboard())

        # Add to search history
        self.db.add_search_history(user_id, username, first_name, api_type, query)

    def make_api_call(self, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
            }

            if 'postalpincode.in' in url:
                headers['Referer'] = 'https://www.postalpincode.in/'

            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logging.error(f"API call failed: {e}")
            return None

    def format_api_response(self, response, api_type, query):
        try:
            json_data = json.loads(response)

            # Special handling for pincode API - SHOW ALL POST OFFICES
            if api_type == 'pincode' and isinstance(json_data, list) and len(json_data) > 0:
                pincode_data = json_data[0]
                formatted = f"Pincode: {query}\n"
                formatted += f"Status: {pincode_data.get('Status', 'Unknown')}\n"
                formatted += f"Message: {pincode_data.get('Message', '')}\n\n"

                post_offices = pincode_data.get('PostOffice', [])
                if post_offices:
                    formatted += "Post Offices:\n"
                    # SHOW ALL POST OFFICES - NO LIMIT
                    for office in post_offices:
                        formatted += f"• {office.get('Name', '')} - {office.get('District', '')}, {office.get('State', '')}\n"
                return formatted

            # Remove unwanted fields
            unwanted_fields = ['credit', 'developer', 'API_BY', 'DEVELOPER', 'TELEGRAM', 'footer', 'MADE_BY', 'api_by', 'made_by']
            if isinstance(json_data, dict):
                for field in unwanted_fields:
                    json_data.pop(field, None)

            # Format JSON nicely
            if json_data:
                formatted_json = json.dumps(json_data, indent=2, ensure_ascii=False)
                return f"```json\n{formatted_json}\n```"

        except json.JSONDecodeError:
            pass

        # If not JSON or empty, return raw response
        clean_response = response.strip()

        if not clean_response:
            return f"No data found for: `{query}`"

        # Clean up response
        clean_response = re.sub(r'<[^>]+>', '', clean_response)
        clean_response = re.sub(r'\s+', ' ', clean_response)
        clean_response = clean_response.strip()

        if len(clean_response) > 2000:
            clean_response = clean_response[:2000] + "...\n\n(Response truncated)"

        return f"```\n{clean_response}\n```"

    def admin_stats(self, chat_id):
        total = self.db.get_total_users()
        banned = self.db.get_banned_users_count()
        searches = self.db.get_total_searches()

        msg = "📊 *User Statistics*\n\n"
        msg += f"👥 *Total Users:* {total}\n"
        msg += f"🚫 *Banned:* {banned}\n"
        msg += f"🔍 *Searches:* {searches}\n\n"
        msg += "🔰 *Developer:* @gokuuuu_1\n"
        msg += "⚡ *Powered By:* DarkGoku"
        self.send_message(chat_id, msg, self.admin_keyboard())

    def admin_search_stats(self, chat_id):
        stats = self.db.get_search_stats()
        msg = "📈 *Search Statistics*\n\n"
        for stat in stats:
            msg += f"• {stat['service_type']}: {stat['count']}\n"
        msg += "\n🔰 *Developer:* @gokuuuu_1\n"
        msg += "⚡ *Powered By:* DarkGoku"
        self.send_message(chat_id, msg, self.admin_keyboard())

    def admin_banned_list(self, chat_id):
        banned = self.db.get_banned_users()
        if not banned:
            self.send_message(chat_id, "✅ No banned users!", self.admin_keyboard())
            return
        msg = "🚫 *Banned Users*\n\n"
        for user in banned:
            msg += f"• `{user['user_id']}` - {user['first_name']}\n  Reason: {user.get('ban_reason', 'No reason')}\n\n"
        msg += "🔰 *Developer:* @gokuuuu_1\n"
        msg += "⚡ *Powered By:* DarkGoku"
        self.send_message(chat_id, msg, self.admin_keyboard())

    def admin_protected_list(self, chat_id):
        protected = self.db.get_protected_numbers()
        if not protected:
            self.send_message(chat_id, "✅ No protected numbers!", self.admin_keyboard())
            return
        msg = "🛡️ *Protected Numbers*\n\n"
        for number in protected:
            msg += f"• `{number['phone_number']}`\n  Reason: {number.get('reason', 'No reason')}\n\n"
        msg += "🔰 *Developer:* @gokuuuu_1\n"
        msg += "⚡ *Powered By:* DarkGoku"
        self.send_message(chat_id, msg, self.admin_keyboard())

    def handle_pending(self, chat_id, user_id, username, first_name, text, pending):
        action = pending['pending_action']
        extra = pending['extra_data']

        if text.lower() in ['❌ cancel', 'cancel']:
            self.db.clear_pending(chat_id)
            self.send_message(chat_id, "❌ Cancelled", self.admin_keyboard())
            return

        if action == 'add_credits_user':
            if text.isdigit():
                self.db.set_pending(chat_id, 'add_credits_amount', text)
                self.send_message(chat_id, "How many credits?", self.cancel_keyboard())
            else:
                self.send_message(chat_id, "❌ Invalid ID. Send numeric ID:", self.cancel_keyboard())

        elif action == 'add_credits_amount':
            if text.isdigit():
                self.db.add_credits(int(extra), int(text))
                self.db.clear_pending(chat_id)
                self.send_message(chat_id, f"✅ Added {int(text)} credits to {extra}", self.admin_keyboard())

        elif action == 'remove_credits_user':
            if text.isdigit():
                self.db.set_pending(chat_id, 'remove_credits_amount', text)
                self.send_message(chat_id, "How many to remove?", self.cancel_keyboard())

        elif action == 'remove_credits_amount':
            if text.isdigit():
                self.db.deduct_credits(int(extra), int(text))
                self.db.clear_pending(chat_id)
                self.send_message(chat_id, f"✅ Removed {int(text)} credits from {extra}", self.admin_keyboard())

        elif action == 'ultimate_credits':
            if text.isdigit():
                self.db.set_credits(int(text), ULTIMATE_CREDITS)
                self.db.clear_pending(chat_id)
                self.send_message(chat_id, f"⚡ Granted {ULTIMATE_CREDITS} credits to {text}", self.admin_keyboard())

        elif action == 'ban_user_id':
            if text.isdigit():
                self.db.set_pending(chat_id, 'ban_user_reason', text)
                self.send_message(chat_id, "Ban reason?", self.cancel_keyboard())

        elif action == 'ban_user_reason':
            self.db.ban_user(int(extra), user_id, text)
            self.db.clear_pending(chat_id)
            self.send_message(chat_id, f"🔨 Banned {extra}\n\nReason: {text}", self.admin_keyboard())

        elif action == 'unban_user':
            if text.isdigit():
                self.db.unban_user(int(text))
                self.db.clear_pending(chat_id)
                self.send_message(chat_id, f"🔓 Unbanned {text}", self.admin_keyboard())

        elif action == 'protect_number_phone':
            if re.match(r'^\d{10}$', text):
                self.db.set_pending(chat_id, 'protect_number_reason', text)
                self.send_message(chat_id, "Protection reason?", self.cancel_keyboard())

        elif action == 'protect_number_reason':
            self.db.protect_number(extra, user_id, text)
            self.db.clear_pending(chat_id)
            self.send_message(chat_id, f"🛡️ Protected {extra}\n\nReason: {text}", self.admin_keyboard())

    def run_polling(self):
        """Main polling loop"""
        print("🤖 ALL OSINT BY GOKU BOT Starting... (Polling Mode)")
        print("🔰 Developer: @gokuuuu_1")
        print("⚡ Powered By: DarkGoku")
        print("📢 Force Join: @darkkk_goku & @Dark_x_gokjuu")
        print("📷 Instagram: __dark_hackerr_")
        print("🚀 Bot is running! Press Ctrl+C to stop.")

        while True:
            try:
                self.get_updates()
                time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Bot stopped by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(5)

# =====================================
# 🎯 MAIN EXECUTION
# =====================================

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        print("⚠️ Please configure BOT_TOKEN at the top of the file")
        exit(1)

    bot = TelegramBot()
    bot.run_polling()t.run_polling()