/* src/pages/NotFoundPage.tsx */
import React from "react";
import { useNavigate } from "react-router-dom";
import { Card } from "../components/common/Card";
import { Button } from "../components/common/Button";
import { Compass } from "lucide-react";
import "./NotFoundPage.css";

export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="notfound-page">
      <div className="notfound-container animate-fade-in">
        <Card className="notfound-card" glow>
          <div className="notfound-content">
            <div className="notfound-icon-wrap">
              <Compass size={48} className="notfound-icon animate-pulse-glow" />
            </div>
            <h1 className="notfound-title">404 - Domain Unmapped</h1>
            <p className="notfound-description">
              The requested address does not represent an active endpoint in this secure environment context.
            </p>
            <div className="notfound-actions">
              <Button variant="primary" onClick={() => navigate("/dashboard")}>
                Return to Safety
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
