import { useState, useEffect } from "react";
import axios from "axios";

export default function Root() {
    const [isLoading, setIsLoading] = useState(true);
    const [showDialog, setShowDialog] = useState(false);
    const [userID, setUserID] = useState("");

    useEffect(() => {
        const isDesktop = () => {
            const userAgent = navigator.userAgent.toLowerCase();
            const isMobile = /mobile|android|iphone|ipad|tablet|blackberry|opera mini/.test(userAgent);
            return !isMobile && typeof window.matchMedia === "function" && matchMedia("(pointer: fine)").matches;
        };

        if (!isDesktop()) {
            setShowDialog(true); 
            setIsLoading(false); 
        } else {
            checkUserID(); 
        }
    }, []);

    const checkUserID = async () => {
        const storedUserID = sessionStorage.getItem("userID");
        if (storedUserID) {
            setUserID(storedUserID);
            setIsLoading(false);
        } else {
            try {
                const response = await axios.get("/api/userid"); 
                const newUserID = response.data.userID;
                sessionStorage.setItem("userID", newUserID);
                setUserID(newUserID);
                setIsLoading(false);
            } catch (error) {
                console.error("Error fetching user ID:", error);
                alert("An error occurred while fetching the user ID. Please try again.");
            }
        }
    };

    const handleStart = () => {
        window.location.href = "/consent";
    };

    if (isLoading) {
        return <div>Loading...</div>; 
    }

    if (showDialog) {
        return (
            <div className="confirm-dialog-overlay">
                <div className="confirm-dialog">
                    <h2>This experiment requires a computer and a mouse.</h2>
                </div>
            </div>
        );
    }

    return (
        <div>
            <h1>Welcome to the Experiment</h1>
            <button onClick={handleStart}>Start</button>
        </div>
    );
}
