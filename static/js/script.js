function sendMail() {
    let parms = {
        fname: document.getElementById("fname").value,
        lname: document.getElementById("lname").value,
        email: document.getElementById("email").value,
        subject: document.getElementById("subject").value,
        message: document.getElementById("message").value
    };

    emailjs.send("service_33r7ee4", "template_mqk5218", parms)
        .then(function(response) {
            alert("Email Sent Successfully!"); // Now it only alerts if email sending succeeds
            console.log("Success!", response);
        })
        .catch(function(error) {
            alert("Failed to send email: " + error.text);
            console.error("Error:", error);
        });
}
