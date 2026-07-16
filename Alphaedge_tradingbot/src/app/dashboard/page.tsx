import DashboardClient from "./DashboardClient"

export default async function DashboardPage() {
  const user = { name: "AlphaEdge User", email: "user@alphaedge.ai", image: null }
  return <DashboardClient user={user} />
}
