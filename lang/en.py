# lang/en.py
"""
English texts for bot
"""

MESSAGES = {
    # ========== MAIN COMMANDS ==========
    'cmd_start': "/start — start the bot",
    'cmd_menu': "/menu — main menu",
    'cmd_id': "/id — show your ID",
    'cmd_search': "/search — find a partner",
    'cmd_stop': "/stop — end chat",
    'cmd_next': "/next — next partner",
    'cmd_profile': "/profile — my profile",
    'cmd_topics': "/topics — my topics",
    'cmd_premium': "/premium — premium subscription",
    'cmd_admin': "/admin — admin panel",

    # ========== WELCOME ==========
    'welcome': "✨ <b>Welcome to Anonymous Chat!</b> ✨\n\n👇 <i>Main features:</i>\n• <b>🔍 Find a partner</b> — find a companion\n• <b>🎯 My topics</b> — choose topics for communication\n• <b>👤 My profile</b> — change name, age, gender, photo\n\n📜 By using the bot, you agree to the <a href='https://tgbot.local-net.ru:8444/oferta.html'>offer</a>.",
    'id_info': "🆔 <b>Your ID:</b> <code>{user_id}</code>\n\n📝 <i>May be needed to contact support</i>",

    # ========== SEARCH ==========
    'search_start': "🔍 <b>Searching for a partner...</b>",
    'search_cancel': "✅ Search stopped.",
    'search_not_found': "❌ You are not searching.",
    'search_premium_choose': "🔍 <b>Choose search type:</b>\n\n👥 <b>Regular search</b> — all users\n👩 <b>Girls only</b>\n👨 <b>Boys only</b>",
    'search_premium_selected': "✅ {search_type} search selected",
    'search_type_normal': "regular",
    'search_type_girls': "girls only",
    'search_type_boys': "boys only",

    # ========== CHAT ==========
    'chat_started': "🎉 <b>Partner found!</b>",
    'chat_started_with_topic': "🎉 <b>Partner found!</b>\n\n🎯 <b>Topic:</b> {topic_emoji} {topic_name}",
    'chat_ended': "✅ <b>Chat ended</b>",
    'chat_ended_ai': "✅ <b>AI chat ended</b>",
    'chat_partner_left': "👋 <b>Partner left the chat</b>",
    'chat_partner_found': "🎉 <b>Собеседник найден!<.b>",
    'chat_already_in': "❌ You are already in a chat!\n\nFirst end the current chat (press '⏹️ End'), then start a new search.",

    # ========== RATINGS AND REPORTS ==========
    'rate_question': "🎯 <b>Rate the quality of communication:</b>",
    'rate_good': "✅ Thank you for your rating!",
    'rate_bad': "👎 Negative rating recorded",
    'rate_already': "❌ You have already rated this partner in this chat",
    'report_question': "⚠️ <b>Report user</b>\n\nChoose the reason for reporting:",
    'report_custom_question': "✏️ <b>Write the reason for your report</b>\n\nDescribe what you didn't like. The report will be sent to moderators.\n\nTo cancel press /cancel",
    'report_sent': "⚠️ Report sent. Moderators will review it.",
    'report_ai': "⚠️ Report received. We will use it to improve the AI.",
    'report_empty': "❌ Report cannot be empty",

    # ========== REPORT REASONS ==========
    'complaint_abuse': "🚫 Harassment",
    'complaint_adult': "🔞 18+ / Obscene",
    'complaint_spam': "💼 Advertising/Spam",
    'complaint_scam': "🎭 Fraud/Scam",
    'complaint_hate': "🗣️ Hate speech",
    'complaint_data': "📵 Personal data",
    'complaint_wrong_gender': "❌ Wrong gender",
    'complaint_fake_male': "👨 Faking as male",
    'complaint_fake_female': "👩 Faking as female",
    'complaint_custom': "✏️ Custom reason",
    'complaint_other': "⚡ Other",

    # ========== PROFILE ==========
    'profile_title': "👤 <b>USER PROFILE</b>\n{'═' * 25}",
    'profile_id': "🆔 <b>ID:</b> <code>{user_id}</code>",
    'profile_username': "📛 <b>Telegram username:</b> {username}",
    'profile_chat_name': "💬 <b>Chat name:</b> {chat_name}",
    'profile_age': "🎂 <b>Age:</b> {age}",
    'profile_gender': "⚧ <b>Gender:</b> {gender}",
    'profile_status': "🔰 <b>Status:</b> {status}",
    'profile_stats_title': "📊 <b>Statistics:</b>",
    'profile_reputation': "• Reputation: {reputation}/100",
    'profile_chats': "• Chats: {chats}",
    'profile_searches': "• Searches: {searches}",
    'profile_messages': "• Messages: {messages}",
    'profile_topics_title': "🎯 <b>Topics:</b>",
    'profile_topics_none': "❌ Not selected",
    'profile_edit_hint': "\n👇 <i>Edit data:</i>",

    # ========== PARTNER PROFILE ==========
    'partner_profile_title': "👤 <b>PARTNER PROFILE</b>\n{'═' * 25}",
    'partner_profile_in_development': "👤 Partner profile (in development)",

    # ========== PROFILE EDITING ==========
    'edit_name_question': "✏️ <b>Enter your chat name:</b>\n\n<i>2 to 20 characters. Other users will see it.</i>",
    'edit_age_question': "🎂 <b>Enter your age:</b>\n\n<i>Only numbers from {min_age} to {max_age}</i>\n<i>Or hide your age with the button below</i>",
    'edit_gender_question': "⚧ <b>Select your gender:</b>\n\n<i>Affects partner search</i>",
    'edit_photo_question': "📸 <b>Set main photo</b>\n\nSend the photo you want as your main profile picture.\n\nTo cancel press the 'Back' button",
    'edit_photo_add': "➕ <b>Add photo</b>\n\nSend a photo to add to your gallery.\n\nTo cancel press the 'Back' button",

    'edit_name_success': "✅ Name saved: {name}",
    'edit_age_success': "✅ Age saved: {age} years old",
    'edit_age_hidden': "✅ Age hidden",
    'edit_gender_success': "✅ Gender set: {gender}",
    'edit_photo_success': "✅ Main photo saved!",
    'edit_photo_add_success': "✅ Photo added! (Total photos: {count})",
    'edit_photo_delete_success': "✅ Photo deleted",
    'edit_photo_no_photos': "❌ No photos to delete",

    'edit_name_error': "❌ Name must be between 2 and 20 characters",
    'edit_name_forbidden': "❌ This name is forbidden",
    'edit_age_error': "❌ Enter only numbers (e.g., 25)",
    'edit_age_range_error': "❌ Age must be between {min_age} and {max_age} years",
    'edit_photo_error': "❌ No photos to delete",

    # ========== PREMIUM ==========
    'premium_info': "💎 <b>PREMIUM SUBSCRIPTION</b>\n{'═' * 20}\n\n🚀 <b>Benefits:</b>\n✅ <b>Priority search</b> — find partners faster\n✅ <b>Search filters</b> — by gender, age, activity\n✅ <b>No ads</b> — clean interface\n✅ <b>Unlimited chatting</b>\n\n💰 <b>Pricing:</b>\n• <b>7 days</b> - {price_week}₽ ({price_week_per_day:.1f}₽/day)\n• <b>1 month</b> - {price_month}₽ ({price_month_per_day:.1f}₽/day) 🔥\n• <b>{months} months</b> - {price_3months}₽ ({price_3months_per_day:.1f}₽/day) 💎\n• <b>1 year</b> - {price_year}₽ ({price_year_per_day:.1f}₽/day) 👑\n\n⚠️ <b>Important:</b> No refunds for subscription cancellation. The subscription remains active until the paid period ends.",
    'premium_already': "💎 <b>You already have premium!</b>\n\nValid until: {until}\n\nThank you for your support! 🙏",
    'premium_features': "💎 <b>PREMIUM FEATURES</b>\n\n🚀 <b>Priority search:</b> Find partners 3x faster\n\n🔍 <b>Search filters:</b> By gender, age, activity\n\n📊 <b>Advanced statistics:</b> Detailed chat analytics\n\n🛡️ <b>Additional protection:</b> Priority support",
    'premium_faq': "❓ <b>FREQUENTLY ASKED QUESTIONS</b>\n\n<b>Q: How is premium activated?</b>\nA: Immediately after successful payment\n\n<b>Q: Can I cancel my subscription?</b>\nA: Yes, within 24 hours after payment\n\n<b>Q: Does auto-renewal work?</b>\nA: No, the subscription does not renew automatically\n\n<b>Q: Is there a trial period?</b>\nA: 1-day trial period for the first subscription",
    'premium_buy_button': "💰 Buy Premium",
    'premium_features_button': "💎 My benefits",

    # ========== ADMIN PANEL ==========
    'admin_pin': "👑 <b>Admin Panel Access</b>\n\n<a href='{admin_url}'>Go to Admin Panel</a>\n\n<b>Your PIN code:</b> <code>{pin}</code>\n\n<i>Code valid for 5 minutes</i>",
    'admin_denied': "⛔ Access denied",

    # ========== BUTTONS ==========
    'btn_search': "🔍 Find a partner",
    'btn_profile': "👤 My profile",
    'btn_topics': "🎯 My topics",
    'btn_premium': "💎 Premium",
    'btn_stats': "📊 Statistics",
    'btn_help': "❓ Help",
    'btn_menu': "🔙 Back to main menu",
    'btn_cancel': "❌ Cancel search",
    'btn_stop': "⏹️ End chat",
    'btn_next': "⏭️ Next",
    'btn_partner_info': "👤 Info",
    'btn_back': "🔙 Back",
    'btn_back_to_profile': "🔙 Back to profile",
    'btn_add_photo': "➕ Add photo",
    'btn_delete_photo': "🗑 Delete photo",

    'btn_rating_good': "👍",
    'btn_rating_bad': "👎",
    'btn_report': "⚠️ Report",

    # ========== USER STATUSES ==========
    'status_admin': "👑 Administrator",
    'status_premium': "💎 Premium",
    'status_user': "👤 User",
    'status_guest': "👋 Guest",
    'status_banned': "⛔ Banned",
    'status_limited': "⚠️ Limited",
    'status_warning': "⚠️ Warning",
    'status_trusted': "✅ Trusted",
    'status_vip': "⭐ High reputation",

    # ========== SEARCH INFO ==========
    'search_status': "🔍 <b>Searching for a partner...</b>\n\n{limit_info}\n👥 <b>In queue:</b> <code>{queue_count}</code> people\n\n<i>To cancel, press the button below</i>",
    'search_limit_guest': "📊 <b>Chats remaining today:</b> {remaining}/{limit}\n🎯 <b>Topics:</b> {topics}",
    'search_limit_premium': "💎 <b>Premium:</b> unlimited\n🎯 <b>Filter:</b> {filter}\n🎯 <b>Topics:</b> {topics}",
    'search_filter_all': "👥 all",
    'search_filter_girls': "👩 girls only",
    'search_filter_boys': "👨 boys only",
}

# ========== ТЕМЫ (ключи из БД) ==========
TOPIC_NAMES = {
    'role_games': 'Role Games',
    'memes': 'Memes',
    'loneliness': 'Loneliness',
    'games': 'Games',
    'flirt': 'Flirt',
    'travel': 'Travel',
    'it': 'IT. Computers',
    'music': 'Music',
    'auto': 'Auto',
    'anime': 'Anime',
    'movies': 'Movies',
    'pets': 'Pets',
    'books': 'Books',
    'sports': 'Sports',
}

TOPIC_EMOJIS = {
    'role_games': '🎭',
    'memes': '😂',
    'loneliness': '🌌',
    'games': '🎮',
    'flirt': '💘',
    'travel': '✈️',
    'it': '💻',
    'music': '🎵',
    'auto': '🚗',
    'anime': '🇯🇵',
    'movies': '🎬',
    'pets': '🐕',
    'books': '📚',
    'sports': '⚽',
}

ERROR_MESSAGES = {
    # Errors
    'error_not_in_chat': "❌ You are not in a chat",
    'error_already_in_chat': "❌ You are already in a chat!\n\nFirst end the current dialogue.",
    'error_already_searching': "⏳ You are already in the search queue.\n\nTo cancel, press '❌ Cancel search'.",
    'error_limit_exceeded': "⚠️ You have run out of messages for today.",
    'error_no_active_session': "You have no active dialogue. Press /search to start.",
    'error_still_searching': "⏳ We are still looking for a partner...",
    'error_not_found': "❌ Partner not found",
    'error_permission_denied': "⛔ Access denied",
    'error_unknown': "❌ DB error. Please try again later.",
    'error_db_error': "❌ Ошибка базы данных. Please try again later.",
    'error_ai_error': "🤖 AI error. Please try again later.",
    'error_ai_limit': "❌ AI message limit reached.",
}
