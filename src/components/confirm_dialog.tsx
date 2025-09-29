import React from 'react';

type ConfirmDialogProps = {
  message: string;
  onConfirm: () => void;
};

// The ConfirmDialog is used to build the basic style for the content of the window that appears at the end of each round.
const ConfirmDialog: React.FC<ConfirmDialogProps> = ({ message, onConfirm }) => {
  return (
    <>
      <div className="confirm-dialog-overlay"></div>
      <div className="confirm-dialog">
        <p>{message}</p>
        <button onClick={onConfirm}>Confirm</button>
      </div>
    </>
  );
};

export default ConfirmDialog;
