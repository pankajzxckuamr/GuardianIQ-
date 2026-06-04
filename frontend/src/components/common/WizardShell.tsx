import React, { ReactNode, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check } from 'lucide-react';
import styles from './WizardShell.module.css';

export interface WizardStep {
  label: string;
}

export interface WizardShellProps {
  steps: WizardStep[];
  currentStep: number;
  onStepClick: (stepIndex: number) => void;
  children: ReactNode;
  mode?: 'strict' | 'tabbed';
}

const WizardShell: React.FC<WizardShellProps> = ({
  steps,
  currentStep,
  onStepClick,
  children,
  mode = 'strict'
}) => {
  // Track previous step to determine animation direction
  const [tuple, setTuple] = useState<[number | null, number]>([null, currentStep]);

  if (tuple[1] !== currentStep) {
    setTuple([tuple[1], currentStep]);
  }

  const prevStep = tuple[0] ?? currentStep;
  const direction = currentStep > prevStep ? 1 : -1;

  const variants = {
    enter: (direction: number) => ({
      x: direction > 0 ? 50 : -50,
      opacity: 0
    }),
    center: {
      zIndex: 1,
      x: 0,
      opacity: 1
    },
    exit: (direction: number) => ({
      zIndex: 0,
      x: direction < 0 ? 50 : -50,
      opacity: 0
    })
  };

  const handleStepClick = (index: number) => {
    if (mode === 'strict' && index > currentStep) {
      return; // Cannot click ahead in strict mode
    }
    onStepClick(index);
  };

  return (
    <div className={styles.container}>
      {/* Header / Step Indicator */}
      <div className={styles.header}>
        <div className={styles.stepsWrapper}>
          {steps.map((step, index) => {
            const isActive = index === currentStep;
            const isCompleted = index < currentStep;
            const isClickable = mode === 'tabbed' || index <= currentStep;
            
            return (
              <React.Fragment key={index}>
                {/* Step Node */}
                <div 
                  className={`${styles.stepNode} ${
                    isClickable ? styles.clickable : styles.notClickable
                  } ${isActive ? styles.active : styles.inactive}`}
                  onClick={() => handleStepClick(index)}
                >
                  <div 
                    className={`${styles.stepCircle} ${
                      isActive 
                        ? styles.active 
                        : isCompleted
                          ? styles.completed
                          : styles.pending
                    }`}
                  >
                    {isCompleted ? <Check size={20} strokeWidth={3} /> : <span>{index + 1}</span>}
                  </div>
                  <span 
                    className={`${styles.stepLabel} ${
                      isActive 
                        ? styles.active 
                        : isCompleted 
                          ? styles.completed 
                          : styles.pending
                    }`}
                  >
                    {step.label}
                  </span>
                </div>

                {/* Connector Line */}
                {index < steps.length - 1 && (
                  <div className={styles.connector}>
                    <div 
                      className={styles.connectorFill} 
                      style={{ width: isCompleted ? '100%' : '0%' }}
                    />
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* Content Area */}
      <div className={styles.contentArea}>
        <AnimatePresence initial={false} custom={direction} mode="wait">
          <motion.div
            key={currentStep}
            custom={direction}
            variants={variants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{
              x: { type: "spring", stiffness: 350, damping: 35 },
              opacity: { duration: 0.25 }
            }}
            className={styles.contentWrapper}
          >
            {children}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
};

export default WizardShell;
