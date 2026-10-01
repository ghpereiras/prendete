import { apiGet } from "./client";

export interface WindowCounts {
  total: number;
  last_24h: number;
  last_7d: number;
  last_30d: number;
}

export interface DailyCount {
  date: string;
  count: number;
}

export interface RecentSignup {
  id: number;
  full_name: string;
  email: string;
  created_at: string;
  login_method: "password" | "google";
  email_verified: boolean;
}

export interface AdminStats {
  generated_at: string;
  users: {
    registered: WindowCounts;
    active: WindowCounts;
    with_password: number;
    google_only: number;
    email_verified: number;
    email_unverified: number;
    locked_out: number;
    with_avatar: number;
    with_push: number;
    language_es: number;
    language_en: number;
    never_engaged: number;
    signups_by_day: DailyCount[];
    recent_signups: RecentSignup[];
  };
  events: {
    created: WindowCounts;
    upcoming: number;
    past: number;
    limited_capacity: number;
    avg_attendees: number;
  };
  polls: {
    created: WindowCounts;
    open: number;
    resolved: number;
    avg_participants: number;
  };
  attendances: WindowCounts;
}

export function getAdminStats(): Promise<AdminStats> {
  return apiGet<AdminStats>("/admin/stats");
}
