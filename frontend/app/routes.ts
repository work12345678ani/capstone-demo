import { type RouteConfig, route, layout, index } from "@react-router/dev/routes";

export default [
  layout("routes/_auth.tsx", [
    route("login", "routes/_auth.login.tsx"),
    route("register", "routes/_auth.register.tsx"),
  ]),
  index("routes/_index.tsx"),
] satisfies RouteConfig;