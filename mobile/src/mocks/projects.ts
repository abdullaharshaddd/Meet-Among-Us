// Design shell data – replace with API data

export interface MockProject {
  id: string;
  name: string;
  workspaceId: string;
}

export const projects: MockProject[] = [
  { id: "project-launch", name: "Spring launch", workspaceId: "ws-orbit" },
  { id: "project-hiring", name: "Hiring plan", workspaceId: "ws-orbit" },
  { id: "project-ops", name: "Operations", workspaceId: "ws-orbit" },
  { id: "project-thesis", name: "Thesis review", workspaceId: "ws-side" },
];

// The mock workspaces are told apart by their position in the list.
export function projectsFor(workspaceIndex: number): MockProject[] {
  const workspaceId = workspaceIndex === 0 ? "ws-orbit" : "ws-side";

  return projects.filter((project) => project.workspaceId === workspaceId);
}

export function projectName(projectId: string): string {
  return projects.find((project) => project.id === projectId)?.name ?? "No project";
}
