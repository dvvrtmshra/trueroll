import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { useAuthStore } from "../../store/auth";
import api from "../../lib/api";
import Layout from "../../components/Layout";
import BucketBar from "../../components/BucketBar";
import StatusChip from "../../components/StatusChip";

interface Bucket {
  bucket: string;
  cap: number;
  used: number;
}

interface CourseDetail {
  id: string;
  name: string;
  level: string;
  approved_intake: number;
  lawful_max: number;
  admitted: number;
  buckets: Bucket[];
  open_flags: number;
  status: string;
}

interface DashboardData {
  courses: CourseDetail[];
  last_upload: {
    id: string;
    filename: string;
    uploaded_at: string;
    rows_accepted: number;
    rows_error: number;
    status: string;
  } | null;
  open_flags: number;
  t3_pending: number;
  t3_deadline: string;
}

export default function CollegeDashboardPage() {
  const user = useAuthStore((s) => s.user) as Record<string, unknown> | null;
  const institutionId = user?.institution_id as string | undefined;

  const { data, isLoading, isError } = useQuery<DashboardData>({
    queryKey: ["college-dashboard", institutionId],
    queryFn: () => api.get(`/institutions/${institutionId}/dashboard`).then((r) => r.data),
    enabled: !!institutionId,
  });

  if (!institutionId) return <Layout><p className="text-red-600">No institution linked to this account.</p></Layout>;
  if (isLoading) return <Layout><p className="text-gray-500">Loading dashboard…</p></Layout>;
  if (isError) return <Layout><p className="text-red-600">Failed to load dashboard.</p></Layout>;

  return (
    <Layout>
      <div className="max-w-5xl">
        <h1 className="text-2xl font-bold text-[#0B2545] mb-6">Dashboard</h1>

        {/* Notification cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {data?.open_flags ? (
            <Link
              to="/flags"
              className="bg-red-50 border border-red-200 rounded-lg p-4 hover:bg-red-100 transition-colors"
            >
              <p className="text-sm text-red-800 font-semibold">{data.open_flags} open flag{data.open_flags !== 1 ? "s" : ""}</p>
              <p className="text-xs text-red-600 mt-1">Click to view clarification requests</p>
            </Link>
          ) : (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-sm text-green-800 font-semibold">No open flags</p>
              <p className="text-xs text-green-600 mt-1">All clear</p>
            </div>
          )}

          {data?.t3_pending ? (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
              <p className="text-sm text-amber-800 font-semibold">{data.t3_pending} students without APAAR ID</p>
              <p className="text-xs text-amber-600 mt-1">Deadline: {data.t3_deadline}</p>
            </div>
          ) : (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-sm text-green-800 font-semibold">All APAAR IDs linked</p>
            </div>
          )}

          {data?.last_upload ? (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-800 font-semibold">Last upload</p>
              <p className="text-xs text-blue-600 mt-1">{data.last_upload.filename}</p>
              <p className="text-xs text-blue-500">{data.last_upload.rows_accepted} accepted · {data.last_upload.rows_error} errors</p>
            </div>
          ) : (
            <Link
              to="/upload"
              className="bg-blue-50 border border-blue-200 rounded-lg p-4 hover:bg-blue-100 transition-colors"
            >
              <p className="text-sm text-blue-800 font-semibold">No uploads yet</p>
              <p className="text-xs text-blue-600 mt-1">Click to upload student data →</p>
            </Link>
          )}
        </div>

        {/* Course cards */}
        <h2 className="text-lg font-semibold text-[#0B2545] mb-3">Your Courses</h2>
        {!data?.courses.length && (
          <p className="text-gray-500">No courses found for 2026-27.</p>
        )}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data?.courses.map((course) => (
            <div key={course.id} className="bg-white border border-[#E2E8F0] rounded-lg p-5 shadow-sm">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-semibold text-[#0B2545]">{course.name}</h3>
                  <p className="text-xs text-gray-500">{course.level} · Intake: {course.approved_intake}</p>
                </div>
                <StatusChip status={course.status} count={course.open_flags} />
              </div>
              {course.buckets.map((b) => (
                <BucketBar key={b.bucket} label={b.bucket} used={b.used} cap={b.cap} />
              ))}
              <p className="text-xs text-gray-400 mt-2">
                Lawful max: {course.lawful_max} · Admitted: {course.admitted}
              </p>
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
