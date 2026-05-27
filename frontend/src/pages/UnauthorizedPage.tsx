/* src/pages/UnauthorizedPage.tsx */
import React from "react";
import { useNavigate } from "react-router-dom";
import { Card } from "../components/common/Card";
import { Button } from "../components/common/Button";
import { ShieldAlert } from "lucide-react";
import "./UnauthorizedPage.css";

export const UnauthorizedPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="unauthorized-page">
      <div className="unauthorized-container animate-fade-in">
        <Card className="unauthorized-card" glow>
          <div className="unauthorized-content">
            <div className="unauthorized-icon-wrap">
              <ShieldAlert size={48} className="unauthorized-icon" />
            </div>
            <h1 className="unauthorized-title">Access Denied</h1>
            <p className="unauthorized-description">
              Your security clear level is insufficient to request this domain resource. 
              Role-based access control (RBAC) constraints are fully active.
            </p>
            <div className="unauthorized-actions">
              <Button variant="primary" onClick={() => navigate("/dashboard")}>
                Return to Safety
              </Button>
              <Button variant="secondary" onClick={() => navigate("/login")}>
                Re-Authenticate
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
