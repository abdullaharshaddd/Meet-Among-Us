// Design shell data – replace with API data

export interface MockPerson {
  id: string;
  name: string;
  // A Guest is a named outsider with no account.
  isGuest: boolean;
}

export const members: MockPerson[] = [
  { id: "user-ayesha", name: "Ayesha Siddiqui", isGuest: false },
  { id: "user-bilal", name: "Bilal Hussain", isGuest: false },
  { id: "user-sara", name: "Sara Khan", isGuest: false },
  { id: "user-hamza", name: "Hamza Raza", isGuest: false },
  { id: "user-noor", name: "Noor Fatima", isGuest: false },
];

export const guests: MockPerson[] = [{ id: "guest-omar", name: "Omar Farooq", isGuest: true }];

export function findPerson(id: string): MockPerson | undefined {
  return [...members, ...guests].find((person) => person.id === id);
}
