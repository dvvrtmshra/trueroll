import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "../../store/auth";
import api from "../../lib/api";
import Layout from "../../components/Layout";
import BucketBar from "../../components/BucketBar";
import SimulatedChip from "../../components/SimulatedChip";

interface Bucket {
  bucket: string;
  cap: number;
  used: number;
}

interface Course {
  id: string;
  name: string;
  level: string;
  approved_intake: number;
  lateral_intake: number;
  buckets: Bucket[];
  lawful_max: number;
  admitted: number;
  status: string;
  open_flags: number;
}

const BUCKET_LABELS: Record<string, string> = {
  REGULAR: "Regular",
  OCI_FN_EXTRA: "OCI / FN Extra",
  CIWGC_EXTRA: "CIWGC Extra",
  EWS: "EWS",
  INTL_PG_EXTRA: "International PG Extra",
  INTL_MGT_EXTRA: "International Management Extra",
  LATERAL: "Lateral",
};

export default function MySeatsPage() {
  const user = useAuthStore((s) => s.user) as Record<string, unknown> | null;
  const institutionId = user?.institution_id as string | undefined;

  const { data: courses, isLoading } = useQuery<Course[]>({
    queryKey: ["college-courses", institutionId],
    queryFn: () => api.get(`/institutions/${institutionId}/courses`).then((r) => r.data),
    enabled: !!institutionId,
  });

  if (isLoading) return <Layout><p className="text-gray-500">Loading…</p></Layout>;

  return (
    <Layout>
      <div className="max-w-3xl">
        <div className="flex items-center gap-3 mb-6">
          <h1 className="text-2xl font-bold text-[#0B2545]">My Seats</h1>
          <SimulatedChip />
        </div>
        <p className="text-xs text-gray-500 mb-6">
          Rules are illustrative and marked "Illustrative: to be confirmed against AICTE rules".
        </p>

        {!courses?.length && (
          <p className="text-gray-500">No courses found for 2026-27.</p>
        )}

        {courses?.map((course) => (
          <div key={course.id} className="bg-white border border-[#E2E8F0] rounded-lg p-5 shadow-sm mb-4">
            <h2 className="font-semibold text-[#0B2545] mb-1">{course.name}</h2>
            <p className="text-xs text-gray-500 mb-4">
              {course.level} · Approved intake: {course.approved_intake}
              {course.lateral_intake > 0 && ` · Lateral: ${course.lateral_intake}`}
            </p>

            {course.buckets.map((b) => {
              const near = b.cap > 0 && b.used / b.cap >= 0.95 && b.used <= b.cap;
              return (
                <div key={b.bucket}>
                  {near && (
                    <div className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded px-3 py-1 mb-1">
                      {BUCKET_LABELS[b.bucket] || b.bucket} seats are nearly full ({b.used}/{b.cap})
                    </div>
                  )}
                  <BucketBar
                    label={BUCKET_LABELS[b.bucket] || b.bucket}
                    used={b.used}
                    cap={b.cap}
                  />
                </div>
              );
            })}

            <div className="mt-3 pt-3 border-t border-gray-100 flex items-center gap-2 text-xs text-gray-500">
              <span>
                Lawful maximum:{" "}
                <span className="font-semibold text-[#0B2545]">{course.lawful_max}</span>
                {" "}(
                {course.buckets.map((b) => b.cap).join(" + ")}
                )
              </span>
              <span>·</span>
              <span>
                Admitted:{" "}
                <span className={course.admitted > course.lawful_max ? "text-red-700 font-semibold" : "font-medium"}>
                  {course.admitted}
                </span>
              </span>
            </div>

            <p className="text-xs text-gray-400 mt-2 italic">
              Illustrative: to be confirmed against AICTE rules
            </p>
          </div>
        ))}
      </div>
    </Layout>
  );
}
