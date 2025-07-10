delete
from
	iosapp.saved_jobs ;

delete
from
	iosapp.users;

delete
from
	iosapp.device_tokens ;

delete
from
	iosapp.user_analytics ;

delete
from
	iosapp.notification_settings ;

delete
from
	iosapp.job_views ;
------------------------------------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------------------------------------
delete
from
	iosapp.notification_stats ;

delete
from
	iosapp.job_notification_history ;

delete
from
	iosapp.user_notification_summary ;

delete
from
	iosapp.notification_delivery_log ;

delete
from
	iosapp.push_notifications ;
------------------------------------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------------------------------------
select
	id,
	email,
	keywords,
	preferred_sources,
	notifications_enabled,
	last_notified_at,
	created_at,
	updated_at
from
	iosapp.users;

select
	id,
	user_id,
	device_id,
	device_token,
	device_info,
	is_active,
	registered_at,
	updated_at
from
	iosapp.device_tokens;