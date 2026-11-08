// Design shell data – replace with API data

export type MockMemberRole = "owner" | "admin" | "member";

export interface MockMember {
  userId: string;
  name: string;
  email: string;
  role: MockMemberRole;
  isEnrolled: boolean;
}

export const orbitMembers: MockMember[] = [
  { userId: "user-ayesha", name: "Ayesha Siddiqui", email: "ayesha@orbitlabs.example", role: "owner", isEnrolled: true },
  { userId: "user-bilal", name: "Bilal Hussain", email: "bilal@orbitlabs.example", role: "admin", isEnrolled: true },
  { userId: "user-sara", name: "Sara Khan", email: "sara@orbitlabs.example", role: "member", isEnrolled: true },
  { userId: "user-hamza", name: "Hamza Raza", email: "hamza@orbitlabs.example", role: "member", isEnrolled: false },
  { userId: "user-noor", name: "Noor Fatima", email: "noor@orbitlabs.example", role: "member", isEnrolled: true },
];
