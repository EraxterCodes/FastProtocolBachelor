pragma solidity >=0.4.22 <0.9.0;

contract Auctions {
    uint256 auctionID = 0;

    struct Auction {
        address seller;
        address[] bidders;
        uint256 winningBid;
    }

    Auction[] auctions;
    mapping(uint256 => Auction) public auctionsList;

    function addAuction() public {
        
    }

    function receive_bids(uint256 memory _id) public payable {
        
    }

    function verify_winning_bid() public {
        
    }

    function send_params() public {
        
    }
}