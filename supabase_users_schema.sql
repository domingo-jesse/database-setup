create table if not exists app_users (
    id uuid primary key default gen_random_uuid(),
    email text unique not null,
    full_name text,
    role text default 'user',
    created_at timestamptz default now()
);
