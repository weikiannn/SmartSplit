-- Enable UUID
create extension if not exists pgcrypto;

-------------------------------------------------------
-- Profiles
-------------------------------------------------------

create table profiles (
    id uuid primary key,
    email text unique not null,
    nickname text not null,
    created_at timestamp default now()
);

-------------------------------------------------------
-- Groups
-------------------------------------------------------

create table groups (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    invite_code uuid default gen_random_uuid(),
    admin_id uuid references profiles(id),
    created_at timestamp default now()
);

-------------------------------------------------------
-- Group Members
-------------------------------------------------------

create table group_members (
    group_id uuid references groups(id) on delete cascade,
    user_id uuid references profiles(id) on delete cascade,
    joined_at timestamp default now(),

    primary key(group_id, user_id)
);

-------------------------------------------------------
-- Expenses
-------------------------------------------------------

create table expenses (

    id uuid primary key default gen_random_uuid(),

    group_id uuid references groups(id) on delete cascade,

    payer_id uuid references profiles(id),

    created_by uuid references profiles(id),

    description text,

    amount decimal,

    currency text,

    split_type text,

    splits jsonb,

    status text default 'active',

    created_at timestamp default now()
);

-------------------------------------------------------
-- Settlements
-------------------------------------------------------

create table settlements (

    id uuid primary key default gen_random_uuid(),

    group_id uuid references groups(id),

    settled_by uuid references profiles(id),

    settled_at timestamp default now()
);