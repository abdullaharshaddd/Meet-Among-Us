import { useEnrollmentStatus } from "@/api/enrollment";

export function useEnrollmentGate() {
  const { data, isLoading } = useEnrollmentStatus();

  return {
    isEnrolled: data?.enrollment_status === "complete",
    isLoading,
  };
}
