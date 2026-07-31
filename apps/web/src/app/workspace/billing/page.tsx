"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchBillingPlans, fetchMe } from "@/lib/api";
import type { BillingPlan, UserMe } from "@/lib/types";

export default function BillingPage() {
  const [me, setMe] = useState<UserMe | null>(null);
  const [plans, setPlans] = useState<BillingPlan[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([fetchMe(), fetchBillingPlans()])
      .then(([profile, planList]) => {
        setMe(profile);
        setPlans(planList);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <p className="text-sm text-[var(--muted)]">加载套餐信息…</p>;
  }

  return (
    <div className="space-y-8 max-w-4xl">
      <div>
        <h1 className="text-2xl font-semibold">我的套餐</h1>
        <p className="text-sm text-[var(--muted)] mt-1">
          当前：<span className="text-[var(--text)]">{me?.plan_label || "标准版"}</span>
          {" · "}
          剩余 {me?.points_remaining.toFixed(1)} / {me?.points_limit.toFixed(0)} 点
        </p>
      </div>

      <section className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {plans.map((plan) => {
          const current = plan.id === me?.plan_id;
          return (
            <div
              key={plan.id}
              className={`card p-5 flex flex-col ${
                current ? "border-[var(--accent)] ring-1 ring-[var(--accent)]" : ""
              }`}
            >
              <div className="font-medium text-lg">{plan.label}</div>
              <div className="text-2xl font-bold mt-2">
                {plan.price_cny > 0 ? `¥${plan.price_cny.toFixed(0)}/月` : "免费"}
              </div>
              <div className="text-sm text-[var(--muted)] mt-1">{plan.points_limit.toFixed(0)} 点/月</div>
              <p className="text-sm text-[var(--muted)] mt-3 flex-1">{plan.description}</p>
              {plan.id === "free" && (
                <p className="text-xs text-[var(--warning)] mt-2">不含「深度推演」方案</p>
              )}
              {current ? (
                <span className="mt-4 text-sm text-[var(--accent)] font-medium">当前套餐</span>
              ) : (
                <p className="mt-4 text-xs text-[var(--muted)]">
                  升级请联系管理员或在 Admin 后台切换套餐
                </p>
              )}
            </div>
          );
        })}
      </section>

      {me?.is_admin && (
        <Link href="/workspace/admin" className="text-sm text-[var(--accent)] hover:underline">
          前往管理后台调整用户套餐 →
        </Link>
      )}

      <div className="card p-5 text-sm text-[var(--muted)]">
        <p className="font-medium text-[var(--text)] mb-2">计费说明</p>
        <ul className="list-disc pl-5 space-y-1">
          <li>点数 = 分析方案基础点 × LLM 引擎系数</li>
          <li>失败任务重试不重复扣点（限可重试错误）</li>
          <li>在线支付接入前，套餐由管理员手动开通</li>
        </ul>
      </div>
    </div>
  );
}
