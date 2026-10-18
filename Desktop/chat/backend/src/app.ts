import express from "express";

import authRoutes from "./routes/authRoutes";
import chatRoutes from "./routes/chatRoutes";
import messageRoutes from "./routes/messageRoutes";
import userRoutes from "./routes/userRoutes";

const app = express();

app.use(express.json());

const PORT = process.env.PORT || 4000;


app.get("/health" , (req , res) =>{
    res.json({status:"ok" , message:"server is running"})  
});




app.use("/api/auth" , authRoutes)
app.use("/api/chats" , chatRoutes)
app.use("/api/messages" , messageRoutes)
app.use("/api/users" , userRoutes)

export default app ;