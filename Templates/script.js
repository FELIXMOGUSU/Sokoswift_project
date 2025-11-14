document.addEventListener('DOMContentLoaded', function() {
    const completeOrderBtn = document.getElementById('complete-order');
    const stkModal = document.getElementById('stk-modal');

    if (completeOrderBtn) {
        completeOrderBtn.addEventListener('click', function(e) {
            e.preventDefault(); // Prevent form submission
            
            // Show the modal
            stkModal.style.display = 'block';

            // To simulate success after a few seconds
            setTimeout(function() {
                stkModal.innerHTML = `
                    <div class="modal-content">
                        <h3 style="color: #00b894;">Payment Successful!</h3>
                        <p>Your order has been confirmed.</p>
                        <p>Order ID: #SS1024</p>
                        <a href="index.html" class="btn">Back to Store</a>
                    </div>
                `;
            }, 5000); // 5 seconds for demo
        });
    }
});

