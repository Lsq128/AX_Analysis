"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { storeAuthSession } from "@/lib/api";

function CallbackContent() {
  const router = useRouter();
  const params = useSearchParams();
  const [error, setError] = useState("");

  useEffect(() => {
    const oauthError = params.get("error");
    if (oauthError) {
      setError(`OAuth 登录失败：${oauthError}`);
      return;
    }

    const token = params.get("access_token");
    const userId = params.get("user_id");
    if (!token || !userId) {
      setError("登录回调缺少 token 信息");
      return;
    }

    storeAuthSession({
      access_token: token,
      user_id: userId,
      display_name: params.get("display_name") || userId,
    });
    router.replace("/workspace");
  }, [params, router]);

  if (error) {
    return (
      <div className="card w-full max-w-md p-8 space-y-4 text-center">
        <p className="text-[var(--danger)]">{error}</p>
        <Link href="/login" className="text-sm text-[var(--accent)]">
          返回登录
        </Link>
      </div>
    );
  }

  return <div className="text-[var(--muted)]">正在完成登录…</div>;
}

export default function LoginCallbackPage() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <Suspense fallback={<div className="text-[var(--muted)]">处理登录回调…</div>}>
        <CallbackContent />
      </Suspense>
    </div>
  );
}
