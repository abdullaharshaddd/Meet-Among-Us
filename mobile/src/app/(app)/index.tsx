import { Redirect } from "expo-router";

// Meetings is home.
export default function AppIndex() {
  return <Redirect href="/(app)/meetings" />;
}
