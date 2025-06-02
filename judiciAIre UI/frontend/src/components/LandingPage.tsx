import { SignIn } from "@clerk/clerk-react";

export default function LandingPage() {
  return (
    <div style={{ margin: "10rem",marginLeft:'35rem',display: "flex", justifyContent: "center" }}>
      <SignIn />
    </div>
  );
}
