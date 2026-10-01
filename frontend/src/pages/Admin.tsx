import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Navigate } from "react-router-dom";
import { getAdminStats, type AdminStats, type WindowCounts } from "../api/admin";
import LoadingPage from "../components/LoadingPage";
import ProportionBar from "../components/ProportionBar";
import { useAuth } from "../context/AuthContext";
import { usePageTitle } from "../context/PageTitleContext";
import { formatDateTime } from "../utils/date";

function WindowRow({ label, counts }: { label: string; counts: WindowCounts }) {
  return (
    <tr>
      <th scope="row">{label}</th>
      <td>{counts.total}</td>
      <td>{counts.last_24h}</td>
      <td>{counts.last_7d}</td>
      <td>{counts.last_30d}</td>
    </tr>
  );
}

export default function Admin() {
  const { t, i18n } = useTranslation();
  const lang = i18n.resolvedLanguage ?? "es";
  const { user } = useAuth();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [error, setError] = useState(false);
  const [slow, setSlow] = useState(false);

  usePageTitle(t("admin.title"));

  useEffect(() => {
    if (!user?.is_admin) return;
    const slowTimer = setTimeout(() => setSlow(true), 4000);
    getAdminStats()
      .then(setStats)
      .catch(() => setError(true))
      .finally(() => clearTimeout(slowTimer));
    return () => clearTimeout(slowTimer);
  }, [user?.is_admin]);

  if (!user?.is_admin) {
    return <Navigate to="/" replace />;
  }
  if (error) {
    return (
      <div className="page">
        <p className="error">{t("admin.error")}</p>
      </div>
    );
  }
  if (!stats) {
    return <LoadingPage slow={slow} />;
  }

  const { users, events, polls } = stats;
  const maxDaily = Math.max(1, ...users.signups_by_day.map((d) => d.count));

  return (
    <div className="page admin-page">
      <p className="hint">
        {t("admin.generatedAt", { date: formatDateTime(stats.generated_at, lang) })}
      </p>

      <section>
        <h2>{t("admin.summary")}</h2>
        <table className="admin-table">
          <thead>
            <tr>
              <th />
              <th>{t("admin.total")}</th>
              <th>{t("admin.last24h")}</th>
              <th>{t("admin.last7d")}</th>
              <th>{t("admin.last30d")}</th>
            </tr>
          </thead>
          <tbody>
            <WindowRow label={t("admin.registeredUsers")} counts={users.registered} />
            <WindowRow label={t("admin.activeUsers")} counts={users.active} />
            <WindowRow label={t("admin.events")} counts={events.created} />
            <WindowRow label={t("admin.polls")} counts={polls.created} />
            <WindowRow label={t("admin.attendances")} counts={stats.attendances} />
          </tbody>
        </table>
        <p className="hint">{t("admin.activeHint")}</p>
      </section>

      <section>
        <h2>{t("admin.signupsChart")}</h2>
        <div className="admin-chart" role="img" aria-label={t("admin.signupsChart")}>
          {users.signups_by_day.map((day) => (
            <div
              key={day.date}
              className="admin-chart-bar"
              style={{ height: `${(day.count / maxDaily) * 100}%` }}
              title={`${day.date}: ${day.count}`}
            />
          ))}
        </div>
      </section>

      <section>
        <h2>{t("admin.usersSection")}</h2>
        <h3>{t("admin.loginMethod")}</h3>
        <ProportionBar
          segments={[
            { label: t("admin.withPassword"), value: users.with_password },
            { label: t("admin.googleOnly"), value: users.google_only },
          ]}
        />
        <p className="hint">{t("admin.loginMethodHint")}</p>
        <h3>{t("admin.emailStatus")}</h3>
        <ProportionBar
          segments={[
            { label: t("admin.verified"), value: users.email_verified },
            { label: t("admin.unverified"), value: users.email_unverified },
          ]}
        />
        <h3>{t("admin.language")}</h3>
        <ProportionBar
          segments={[
            { label: "Español", value: users.language_es },
            { label: "English", value: users.language_en },
          ]}
        />
        <ul className="admin-facts">
          <li>{t("admin.lockedOut")}: <strong>{users.locked_out}</strong></li>
          <li>{t("admin.neverEngaged")}: <strong>{users.never_engaged}</strong></li>
          <li>{t("admin.withAvatar")}: <strong>{users.with_avatar}</strong></li>
          <li>{t("admin.withPush")}: <strong>{users.with_push}</strong></li>
        </ul>
      </section>

      <section>
        <h2>{t("admin.eventsSection")}</h2>
        <ProportionBar
          segments={[
            { label: t("admin.upcoming"), value: events.upcoming },
            { label: t("admin.past"), value: events.past },
          ]}
        />
        <ul className="admin-facts">
          <li>{t("admin.avgAttendees")}: <strong>{events.avg_attendees}</strong></li>
          <li>{t("admin.limitedCapacity")}: <strong>{events.limited_capacity}</strong></li>
        </ul>
        <h3>{t("admin.pollsSection")}</h3>
        <ProportionBar
          segments={[
            { label: t("admin.pollsOpen"), value: polls.open },
            { label: t("admin.pollsResolved"), value: polls.resolved },
          ]}
        />
        <ul className="admin-facts">
          <li>{t("admin.avgParticipants")}: <strong>{polls.avg_participants}</strong></li>
        </ul>
      </section>

      <section>
        <h2>{t("admin.recentSignups")}</h2>
        <ul className="admin-recent">
          {users.recent_signups.map((signup) => (
            <li key={signup.id}>
              <div>
                <strong>{signup.full_name}</strong>
                <span className="hint">{signup.email}</span>
              </div>
              <div className="hint">
                {formatDateTime(signup.created_at, lang)} ·{" "}
                {signup.login_method === "google" ? t("admin.googleOnly") : t("admin.withPassword")}
                {!signup.email_verified && ` · ${t("admin.unverified")}`}
              </div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
