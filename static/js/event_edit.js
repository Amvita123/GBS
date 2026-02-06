   // Add new rule
   function AddNewRule(event) {
    const timestamp = new Date().getTime(); 
    const newRuleHTML = `
    <div class="d-flex align-items-start mb-2 rule-container" id="rule_new_${timestamp}">
        <textarea class="form-control me-2" name="rules" placeholder="Describe your detail here ..." rows="2" required></textarea>
        <button type="button" class="btn btn-danger btn-sm" onclick="DeleteRule('${timestamp}')">
            <i class="fa-solid fa-trash"></i>
        </button>
    </div>
    `; 
    const rule_div = document.getElementById(event);
    if(rule_div){
        // rule_div.innerHTML += newRuleHTML;
        rule_div.insertAdjacentHTML("beforeend", newRuleHTML);
    }
    else {
        console.log("div not found: " + event);
    }
}


function DeleteRule(rule_id) {
    let ruleElement = document.getElementById('rule_' + rule_id);
    if(!ruleElement) {
        ruleElement = document.getElementById('rule_new_' + rule_id);
    }
    
    if (ruleElement) {
        if (confirm('Are you sure you want to delete this detail?')) {
            ruleElement.style.transition = 'opacity 0.3s';
            ruleElement.style.opacity = '0';
            setTimeout(() => {
                ruleElement.remove();
                updateRuleCount();
            }, 300);
        }
    } else {
        console.warn('Rule element not found:', rule_id);
    }
}


function updateRuleCount() {
    const ruleCount = document.querySelectorAll('.rule-container').length;
    console.log('Remaining rules:', ruleCount);
    
    const countElement = document.getElementById('ruleCount');
    if (countElement) {
        countElement.textContent = ruleCount;
    }
}

// hyperlink handle

// function AddNewHyperLink(){
//     const timestamp = new Date().getTime();
//
//     const newRuleHTML = `
//     <div class="d-flex align-items-start my-3 rule-container" id="new_hyperlink_${timestamp}">
//         <input type="url" class="form-control me-2" name="booking_link" placeholder="event booking hyperlink" required>
//         <button type="button" class="btn btn-danger btn-sm" onclick="DeleteHyperLink('${timestamp}')">
//             <i class="fa-solid fa-trash"></i>
//         </button>
//     </div>
//     `;
//
//     const hyper_div = document.getElementById("new_hyperlink");
//     if(hyper_div){
//         hyper_div.insertAdjacentHTML("beforeend", newRuleHTML);
//         // rule_div.innerHTML += newRuleHTML;
//     }
//     else {
//         alert("something wrong");
//     }
//
//
// }

function AddNewHyperLink() {
    const timestamp = new Date().getTime();

    // Create new hyperlink input with a unique ID
    const newHyperlinkHTML = `
    <div class="d-flex align-items-start my-3 rule-container" id="new_hyperlink_${timestamp}">
       <div class="d-flex gap-2 flex-grow-1">
        <input type="text" class="form-control" placeholder="Link text label" name="booking_link_label"  required>
        <input type="url" class="form-control " name="booking_link" placeholder="Event booking hyperlink" required>
        <button type="button" class="btn btn-danger btn-sm" onclick="DeleteHyperLink('${timestamp}')"  style="height: 100%;">
            <i class="fa-solid fa-trash"></i>
        </button>
        </div>
    </div>`;

    // Get the container where new hyperlinks will be added
    const hyperlinkContainer = document.getElementById("new_hyperlink");

    if (hyperlinkContainer) {
        hyperlinkContainer.insertAdjacentHTML("beforeend", newHyperlinkHTML);
    } else {
        console.error("Error: Could not find 'new_hyperlink' container.");
        alert("Something went wrong! Please try again.");
    }
}


function DeleteHyperLink(element_id){
    console.log("delete hyper link")
    let ruleElement = document.getElementById('new_hyperlink_' + element_id);

    if(!ruleElement) {
        ruleElement = document.getElementById('new_hyperlink_' + element_id);
    }

    if (ruleElement) {
        if (confirm('Are you sure you want to delete Hyperlink ?')) {
            ruleElement.style.transition = 'opacity 0.3s';
            ruleElement.style.opacity = '0';

            setTimeout(() => {
                ruleElement.remove();
                updateRuleCount();
            }, 300);
        }
    } else {
        alert('Rule element not found');
    }
}
