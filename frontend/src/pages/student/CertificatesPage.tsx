import { useQuery } from "@tanstack/react-query";
import Layout from "../../components/Layout";
import api from "../../lib/api";

interface Cert {
  id: string;
  credential_type: string;
  issued_at: string;
  revoked: boolean;
  download_url: string;
}

export default function CertificatesPage() {
  const { data = [], isLoading } = useQuery<Cert[]>({
    queryKey: ["my-certificates"],
    queryFn: () => api.get("/credentials/certificates").then((r) => r.data),
  });

  function handleDownload(cert: Cert) {
    api.get(cert.download_url).then((r) => {
      const blob = new Blob([JSON.stringify(r.data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `trueroll_cert_${cert.id.slice(-8)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    });
  }

  return (
    <Layout>
      <div className="max-w-sm mx-auto mt-6">
        <h1 className="text-lg font-bold text-[#0B2545] mb-4">Certificates</h1>
        {isLoading ? (
          <p className="text-sm text-gray-400">Loading…</p>
        ) : data.length === 0 ? (
          <p className="text-sm text-gray-400">No certificates yet. Your college issues them on graduation.</p>
        ) : (
          <div className="space-y-3">
            {data.map((cert) => (
              <div key={cert.id} className="bg-white rounded-xl border border-[#E2E8F0] p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm font-medium text-[#0B2545] capitalize">{cert.credential_type} certificate</p>
                    <p className="text-xs text-gray-500">Issued {new Date(cert.issued_at).toLocaleDateString()}</p>
                    {cert.revoked && (
                      <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded mt-1 inline-block">Revoked</span>
                    )}
                  </div>
                  {!cert.revoked && (
                    <button
                      onClick={() => handleDownload(cert)}
                      className="text-sm text-[#0B2545] hover:underline font-medium"
                    >
                      Download
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
