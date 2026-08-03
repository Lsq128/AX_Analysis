"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  fetchAdminStats,
  fetchAdminUsers,
  fetchBillingPlans,
  fetchMe,
  updateUserQuota,
} from "@/lib/api";
import { useBillingEnabled } from "@/hooks/useBillingEnabled";
import type { AdminStats, AdminUser, BillingPlan, UserMe } from "@/lib/types";

export default function AdminPage() {
  const router = useRouter();
  const billingEnabled = useBillingEnabled();
  const [me, setMe] = useState<UserMe | null>(null);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [plans, setPlans] = useState<BillingPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyUser, setBusyUser] = useState<string | null>(null);

  async function reload() {
    const [profile, planList, userList, adminStats] = await Promise.all([
      fetchMe(),
      fetchBillingPlans(),
      fetchAdminUsers(),
      fetchAdminStats(),
    ]);
    setMe(profile);
    setPlans(planList);
    setUsers(userList);
    setStats(adminStats);
  }

  useEffect(() => {
    if (billingEnabled === false) {
      router.replace("/workspace");
      return;
    }
    if (billingEnabled !== true) return;

    reload()
      .catch((e) => setError((e as Error).message))
      .finally(() => setLoading(false));
  }, [billingEnabled, router]);

  async function onChangePlan(userId: string, planId: string) {
    setBusyUser(userId);
    setError("");
    try {
      const updated = await updateUserQuota(userId, { plan_id: planId });
      setUsers((prev) => prev.map((u) => (u.user_id === userId ? updated : u)));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusyUser(null);
    }
  }

  async function onResetUsage(userId: string) {
    setBusyUser(userId);
    setError("");
    try {
      const updated = await updateUserQuota(userId, { reset_usage: true });
      setUsers((prev) => prev.map((u) => (u.user_id === userId ? updated : u)));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusyUser(null);
    }
  }

  if (billingEnabled === false) {
    return <p className="text-sm text-[var(--muted)]">计费已关闭，正在返回工作台…</p>;
  }

  if (billingEnabled === null || loading) {
    return <p className="text-sm text-[var(--muted)]">加载管理面板…</p>;
  }

  if (!me?.is_admin) {
    return (
      <div className="card p-8 text-center">
        <h1 className="text-lg font-medium">无权访问</h1>
        <p className="text-sm text-[var(--muted)] mt-2">需要管理员账号才能查看此页面。</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">管理后台</h1>
        <p className="text-sm text-[var(--muted)] mt-1">用户配额与套餐管理</p>
      </div>

      {error && (
        <div className="rounded-lg border border-[var(--danger)] bg-[var(--danger)]/10 px-4 py-3 text-sm">
          {error}
        </div>
      )}

      {stats && (
        <section className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StatCard label="注册用户" value={String(stats.user_count)} />
          <StatCard label="分析任务" value={String(stats.job_count)} />
          <StatCard label="累计消耗点数" value={stats.total_points_used.toFixed(1)} />
        </section>
      )}

      <section>
        <h2 className="text-sm font-medium text-[var(--muted)] mb-3">套餐目录</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {plans.map((plan) => (
            <div key={plan.id} className="card p-4">
              <div className="font-medium">{plan.label}</div>
              <div className="text-sm text-[var(--muted)] mt-1">{plan.description}</div>
              <div className="text-sm mt-3">
                {plan.points_limit.toFixed(0)} 点/月 · ¥{plan.price_cny.toFixed(0)}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-sm font-medium text-[var(--muted)] mb-3">用户列表</h2>
        {users.length === 0 ? (
          <p className="text-sm text-[var(--muted)]">暂无用户数据。</p>
        ) : (
          <div className="card overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--border)] text-left text-[var(--muted)]">
                  <th className="p-3 font-medium">用户</th>
                  <th className="p-3 font-medium">套餐</th>
                  <th className="p-3 font-medium">用量</th>
                  <th className="p-3 font-medium">操作</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.user_id} className="border-b border-[var(--border)] last:border-0">
                    <td className="p-3">
                      <div className="font-medium">{user.display_name}</div>
                      <div className="text-xs text-[var(--muted)]">{user.user_id}</div>
                    </td>
                    <td className="p-3">
                      <select
                        className="rounded-md border border-[var(--border)] bg-[var(--surface-2)] px-2 py-1"
                        value={user.plan_id}
                        disabled={busyUser === user.user_id}
                        onChange={(e) => onChangePlan(user.user_id, e.target.value)}
                      >
                        {plans.map((plan) => (
                          <option key={plan.id} value={plan.id}>
                            {plan.label}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="p-3">
                      {user.points_used.toFixed(1)} / {user.points_limit.toFixed(0)}
                      <div className="text-xs text-[var(--muted)]">
                        剩余 {user.points_remaining.toFixed(1)} 点
                      </div>
                    </td>
                    <td className="p-3">
                      <button
                        type="button"
                        className="text-[var(--accent)] hover:underline disabled:opacity-50"
                        disabled={busyUser === user.user_id}
                        onClick={() => onResetUsage(user.user_id)}
                      >
                        重置用量
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="card p-4">
      <div className="text-sm text-[var(--muted)]">{label}</div>
      <div className="text-2xl font-semibold mt-1">{value}</div>
    </div>
  );
}
